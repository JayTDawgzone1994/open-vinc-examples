#include <vinc/vinc.hpp>
#include <vinc_messages/CounterSample.hpp>
#include <vinc_messages/GetCountRequest.hpp>
#include <vinc_messages/GetCountResponse.hpp>

#include <cstdint>
#include <iostream>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

class LogPublisher final
    : public vinc::BaseModule<vinc::RunMode::FrameworkLoop> {
public:
    LogPublisher() : BaseModule("sender") {
    }

    vinc::Result<void> on_start(const std::vector<std::string>&) override {
        auto publisher = context.advertise<vinc::CounterSample>("tutorial/counter");
        if (!publisher) {
            return std::unexpected(publisher.error());
        }

        publisher_.emplace(std::move(*publisher));
        write_log(vinc::log::Level::Info, "sender started");
        std::cout << "ready sender" << std::endl;
        return {};
    }

    vinc::Result<std::int32_t> module_interface(std::vector<std::string> args) override {
        if (!args.empty() && args.front() == get_module_name()) {
            args.erase(args.begin());
        }

        if (args.size() == 1 && args.front() == "send") {
            return send_message();
        }

        if ((args.size() == 1 || args.size() == 2) && args.front() == "count") {
            return request_count(args.size() == 2 ? args[1] : "receiver");
        }

        if (args.size() == 1 && args.front() == "trace") {
            const bool enabled = context.log.enabled(vinc::log::Level::Debug);
            write_log(vinc::log::Level::Debug, "trace detail");
            std::cout << "trace debug_enabled=" << enabled << std::endl;
            return 0;
        }

        write_log(vinc::log::Level::Warn, "unknown sender command");
        std::cout << "Usage: sender [send|count [target]|trace]" << std::endl;
        return 1;
    }

    vinc::Result<void> on_stop() override {
        publisher_.reset();
        write_log(vinc::log::Level::Info, "sender stopped");
        std::cout << "stopped sender" << std::endl;
        return {};
    }

private:
    void write_log(vinc::log::Level level, std::string_view text) {
        auto logged = context.log.write(level, text);
        if (!logged) {
            std::cerr << "Log rejected: " << vinc::error_to_string(logged.error()) << std::endl;
        }
    }

    std::int32_t request_count(const std::string& target) {
        auto request = vinc::make_message<vinc::GetCountRequest>();
        auto submitted = context.call_rpc<vinc::GetCountRequest, vinc::GetCountResponse>(
            target, "get_count", *request, {},
            [this](vinc::Result<vinc::rpc::RpcReply<vinc::GetCountResponse>> reply) {
                on_count_reply(std::move(reply));
            });
        if (!submitted) {
            write_log(vinc::log::Level::Error,
                      "RPC request failed: " + vinc::error_to_string(submitted.error()));
            std::cerr << "RPC failed: " << vinc::error_to_string(submitted.error()) << std::endl;
            return 1;
        }

        return 0;
    }

    void on_count_reply(vinc::Result<vinc::rpc::RpcReply<vinc::GetCountResponse>> reply) {
        if (!reply) {
            write_log(vinc::log::Level::Error,
                      "RPC request failed: " + vinc::error_to_string(reply.error()));
            std::cerr << "RPC failed: " << vinc::error_to_string(reply.error()) << std::endl;
            return;
        }

        if (reply->status.code != 0) {
            write_log(vinc::log::Level::Error, "RPC rejected: " + reply->status.reason);
            std::cerr << "RPC rejected: " << reply->status.reason << std::endl;
            return;
        }

        write_log(vinc::log::Level::Info,
                  "RPC count=" + std::to_string(reply->response->data().received.get()));
        std::cout << "RPC received=" << reply->response->data().received.get() << std::endl;
    }

    std::int32_t send_message() {
        write_log(vinc::log::Level::Debug, "sending sequence=" + std::to_string(next_sequence_));
        auto message = vinc::make_message<vinc::CounterSample>();
        message->data().sequence = next_sequence_;
        auto published = publisher_->push(*message);
        if (!published) {
            std::cerr << vinc::error_to_string(published.error()) << std::endl;
            return 1;
        }

        ++next_sequence_;
        return 0;
    }

    std::optional<vinc::message_bus::Publisher<vinc::CounterSample>> publisher_;
    std::uint64_t next_sequence_ = 1;
};

REGISTER_MODULE(LogPublisher, "logPublisher")
