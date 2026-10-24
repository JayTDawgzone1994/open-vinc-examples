// External consumer test: use public Manager/OutputHub APIs, never framework detail.
#include <vinc/module/host/module_manager.hpp>

#include <chrono>
#include <filesystem>
#include <iostream>
#include <map>
#include <string>
#include <thread>

namespace {
using Clock = std::chrono::steady_clock;
constexpr auto operation_timeout = std::chrono::seconds(5);
constexpr auto observation_interval = std::chrono::milliseconds(10);

bool fail(const std::string& message) {
    std::cerr << "FAIL: " << message << '\n';
    return false;
}

bool checked(vinc::Result<void> result) {
    if (!result) {
        return fail(vinc::error_to_string(result.error()));
    }

    return true;
}

bool command(vinc::ModuleManager& manager, const char* name,
             std::vector<std::string> arguments, std::int32_t expected) {
    auto result = manager.command(name, std::move(arguments), Clock::now() + operation_timeout);
    if (!result) {
        return fail(vinc::error_to_string(result.error()));
    }

    if (*result != expected) {
        return fail("unexpected command result");
    }

    return true;
}

class Output {
public:
    bool wait_for(vinc::output_hub::Subscription& subscription,
                  std::uint64_t pid, const std::string& marker) {
        const auto deadline = Clock::now() + operation_timeout;
        while (Clock::now() < deadline) {
            const auto batch = subscription.take();
            if (batch.skipped.bytes != 0 || batch.skipped.events != 0) {
                return fail("test lost captured output");
            }

            for (const auto& event : batch.events) {
                if (event->kind == vinc::output_hub::EventKind::Data) {
                    // Separate process streams; a pipe event can contain only part of a line.
                    text_[{event->source->pid, event->source->stream}] += event->bytes;
                    std::cout << event->bytes;
                }
            }

            if (text_[{pid, vinc::output_hub::Stream::Stdout}].find(marker) != std::string::npos) {
                return true;
            }

            std::this_thread::sleep_for(observation_interval);
        }

        return fail("output deadline: " + marker);
    }

private:
    std::map<std::pair<std::uint64_t, vinc::output_hub::Stream>, std::string> text_;
};

bool shutdown(vinc::ModuleManager& manager) {
    manager.begin_shutdown();
    if (!checked(manager.wait_shutdown(Clock::now() + operation_timeout))) {
        return false;
    }

    for (const auto& module : manager.snapshots()) {
        if (module.state != vinc::ModuleState::Stopped || !module.last_exit ||
            module.last_exit->kind != vinc::osal::ExitKind::Code || module.last_exit->value != 0 ||
            module.last_failure || module.cleanup_failure || module.restarts != 0) {
            return fail("shutdown did not confirm a clean OS process exit");
        }
    }

    if (manager.output_hub().stats().active_captures != 0) {
        return fail("output capture remained active after shutdown");
    }

    std::cout << "PASS OS-confirmed exits and drained captures\n";
    return true;
}

bool run(const std::filesystem::path& host, const std::filesystem::path& publisher,
         const std::filesystem::path& subscriber) {
    auto created = vinc::ModuleManager::create({}, host);
    if (!created) {
        return fail(vinc::error_to_string(created.error()));
    }

    // Manager destruction also stops/reaps owned children on any failure return below.
    auto manager = std::move(*created);
    auto captured = manager->output_hub().subscribe();
    if (!captured) {
        return fail(vinc::error_to_string(captured.error()));
    }

    if (!checked(manager->register_module_type({"counterSubscriber", subscriber, {}})) ||
        !checked(manager->register_module_type({"counterPublisher", publisher, {}}))) {
        return false;
    }

    auto receiver_mid = manager->start_module("counterSubscriber");
    if (!receiver_mid) {
        return fail(vinc::error_to_string(receiver_mid.error()));
    }

    if (!checked(manager->wait_running(*receiver_mid, Clock::now() + operation_timeout))) {
        return false;
    }

    auto sender_mid = manager->start_module("counterPublisher");
    if (!sender_mid) {
        return fail(vinc::error_to_string(sender_mid.error()));
    }

    if (!checked(manager->wait_running(*sender_mid, Clock::now() + operation_timeout))) {
        return false;
    }

    const auto receiver = manager->inspect(*receiver_mid);
    const auto sender = manager->inspect(*sender_mid);
    if (!receiver || !sender || receiver->pid == 0 || sender->pid == 0 ||
        receiver->pid == sender->pid || receiver->mid == sender->mid ||
        receiver->name != "receiver" || sender->name != "sender") {
        return fail("module process identities are not distinct");
    }

    std::cout << "PASS isolated processes: receiver=" << receiver->pid
              << " sender=" << sender->pid << '\n';
    Output output;

    // Invalid input is a command failure, not a Module failure, and must not publish.
    if (!command(*manager, "sender", {"sender", "invalid"}, 1) ||
        !command(*manager, "sender", {"sender", "send"}, 0) ||
        !output.wait_for(*captured, receiver->pid, "received sequence=1 publisher=sender")) {
        return false;
    }

    // Wait for each actual callback before sending again; no fixed delivery sleep.
    if (!command(*manager, "sender", {"send"}, 0) ||
        !output.wait_for(*captured, receiver->pid, "received sequence=2 publisher=sender") ||
        !command(*manager, "receiver", {"receiver", "status"}, 0) ||
        !output.wait_for(*captured, receiver->pid, "received=2")) {
        return false;
    }

    if (!checked(manager->wait_running(*sender_mid, Clock::now() + operation_timeout))) {
        return false;
    }

    std::cout << "PASS payload, publisher metadata and recoverable command failure\n";
    return shutdown(*manager);
}
}

int main(int argc, char** argv) {
    if (argc != 4) {
        return 2;
    }

    // Reusing the same central/name after a full teardown checks normal resource reuse.
    for (int cycle = 0; cycle < 2; ++cycle) {
        if (!run(std::filesystem::absolute(argv[1]), std::filesystem::absolute(argv[2]),
                 std::filesystem::absolute(argv[3]))) {
            return 1;
        }
    }

    return 0;
}
