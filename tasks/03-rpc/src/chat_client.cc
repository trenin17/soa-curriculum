#include <iostream>
#include <memory>
#include <string>
#include <chrono>
#include <thread>
#include <vector>

#include <grpcpp/grpcpp.h>

#include "chat.grpc.pb.h"
#include "chat.pb.h"

using grpc::Channel;
using grpc::ClientContext;
using grpc::Status;
using chat::Handler;
using chat::EnrollRequest;
using chat::EnrollResponse;
using chat::Empty;
using chat::Event;
using chat::VoteCandidate;
using chat::Role;
using chat::Username;

enum {
    Failed = -1,
    GameStarted = 1,
    Voting = 2,
    MafiaTurn = 3,
    ComissarTurn = 4,
    GameEndedMafia = 5,
    GameEndedCitizens = 6
};

class AggregatedEvent {
 public:
    AggregatedEvent(int failed): status(failed), players(), active() {}

    AggregatedEvent(int status, 
                    std::vector<std::string> players,
                    std::vector<std::string> active):
        status(status), players(players), active(active) {}

    int status;
    std::vector<std::string> players;
    std::vector<std::string> active;
};

class ChatClient {
 public:
    ChatClient(std::shared_ptr<Channel> channel)
        : stub_(Handler::NewStub(channel)) {}

    std::string Enroll(const std::string& user) {
        EnrollRequest request;
        request.set_user(user);

        EnrollResponse response;

        ClientContext context;

        Status status = stub_->Enroll(&context, request, &response);

        if (status.ok()) {
        return response.message();
        } else {
        std::cout << status.error_code() << ": " << status.error_message()
                    << std::endl;
        return "RPC failed";
        }
    }

    AggregatedEvent PollEvents() {
        ClientContext context;

        Empty request;
        Event response;

        Status status = stub_->PollEvents(&context, request, &response);

        if (status.ok()) {
            return AggregatedEvent(response.n_event(), 
                std::vector<std::string>(response.players().begin(), response.players().end()),
                std::vector<std::string> (response.active().begin(), response.active().end()));
        } else {
            std::cout << status.error_code() << ": " << status.error_message()
                        << std::endl;
            return AggregatedEvent(Failed);
        }
    }

    void Vote(const std::string& pick) {
        ClientContext context;
        VoteCandidate request;
        Empty response;

        Status status = stub_->Vote(&context, request, &response);

        if (!status.ok()) {
            std::cout << status.error_code() << ": " << status.error_message()
                        << std::endl;
        }

    }

    void GetRole(const std::string& name) {
        ClientContext context;
        Username request;
        request.set_name(name);
        Role response;

        Status status = stub_->GetRole(&context, request, &response);

        if (!status.ok()) {
            std::cout << status.error_code() << ": " << status.error_message()
                        << std::endl;
            return;
        }
        std::cout << "You are " << response.role() << std::endl;
        if (response.role() == "Mafia") {
            role_ = std::make_unique<Mafia>();
        }
        
        if (response.role() == "Comissar") {
            role_ = std::make_unique<Comissar>();
        }

        if (response.role() == "Citizen") {
            role_ = std::make_unique<Citizen>();
        }
    }

    void Act(int event) {
        role_->Act(event);
    }

 private:
    std::unique_ptr<Handler::Stub> stub_;

    class Player {
     public:
        virtual void Act(int event) {}
    };

    class Mafia: public Player {
     public:
        void Act(int event) override {
        }
    };

    class Comissar: public Player {
     public:
        void Act(int event) override {
        }
    };

    class Citizen: public Player {
     public:
        void Act(int event) override {}
    };

    std::unique_ptr<Player> role_;
};

int main() {
    std::string ip, port, name;
    std::cout << "Enter ip: ";
    std::cin >> ip;
    std::cout << "Enter port: ";
    std::cin >> port;
    std::cout << "Enter your name: ";
    std::cin >> name;

    ChatClient handler(
    grpc::CreateChannel(ip + ":" + port, grpc::InsecureChannelCredentials()));

    std::string response = handler.Enroll(name);
    std::cout << response << std::endl;

    while (true) {
        const AggregatedEvent event = handler.PollEvents();
        if (event.status == Failed) break;
        switch (event.status)
        {
        case GameStarted:
            std::cout << "The game has started!" << std::endl;
            handler.GetRole(name);
            break;
        
        case Voting: {
            int pick, cnt = 0;
            while (event.active[pick = random() % event.active.size()] != name);
            std::cout << "Active: ";
            for (const auto& p : event.active) {
                if (cnt) {
                    std::cout << ", ";
                }
                cnt++;
                std::cout << p;
            }
            std::cout << "Voting for " << event.active[pick];
            handler.Vote(event.active[pick]);
            break;
        }

        case MafiaTurn:
            handler.Act(event.status);
            break;
        
        case ComissarTurn:
            handler.Act(event.status);
            break;
        
        case GameEndedMafia:
            std::cout << "The game is over. Mafia won!" << std::endl;
            break;

        case GameEndedCitizens:
            std::cout << "The game is over. Citizens won!" << std::endl;
            break;

        default:
            break;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    return 0;
}