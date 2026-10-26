#include <vinc/vinc.hpp>
#include <vinc_messages/CounterSample.hpp>
#include <vinc_messages/GetCountRequest.hpp>
#include <vinc_messages/GetCountResponse.hpp>

#include <cstdint>
#include <iostream>
#include <optional>
#include <string>
#include <utility>
#include <vector>

class RpcPublisher final
    : public vinc::BaseModule<vinc::RunMode::FrameworkLoop> {
public:
    RpcPublisher() : BaseModule("sender") {
    }

    vinc::Result<void> on_start(const std::vector<std::string>&) override {
        auto publisher = context.advertise<vinc::CounterSample>("tutorial/counter");
        if (!publisher) {
            return std::unexpected(publisher.error());
        }

        publisher_.emplace(std::move(*publisher));
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

        if (args.size() == 1 && args.front() == "count") {
            return request_count();
        }

        std::cout << "Usage: sender [send|count]" << std::endl;
        return 1;
    }

    vinc::Result<void> on_stop() override {
        publisher_.reset();
        std::cout << "stopped sender" << std::endl;
        return {};
    }

private:
    std::int32_t request_count() {
        auto request = vinc::make_message<vinc::GetCountRequest>();
        auto submitted = context.call_rpc<vinc::GetCountRequest, vinc::GetCountResponse>(
            "receiver", "get_count", *request, {},
            [this](vinc::Result<vinc::rpc::RpcReply<vinc::GetCountResponse>> reply) {
                on_count_reply(std::move(reply));
            });
        if (!submitted) {
            std::cerr << "RPC failed: " << vinc::error_to_string(submitted.error()) << std::endl;
            return 1;
        }

        return 0;
    }

    void on_count_reply(vinc::Result<vinc::rpc::RpcReply<vinc::GetCountResponse>> reply) {
        if (!reply) {
            std::cerr << "RPC failed: " << vinc::error_to_string(reply.error()) << std::endl;
            return;
        }

        if (reply->status.code != 0) {
            std::cerr << "RPC rejected: " << reply->status.reason << std::endl;
            return;
        }

        std::cout << "RPC received=" << reply->response->data().received.get() << std::endl;
    }

    std::int32_t send_message() {
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

REGISTER_MODULE(RpcPublisher, "rpcPublisher")
