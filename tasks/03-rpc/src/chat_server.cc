#include <iostream>
#include <memory>
#include <string>
#include <set>
#include <map>

#include <grpcpp/ext/proto_server_reflection_plugin.h>
#include <grpcpp/grpcpp.h>
#include <grpcpp/health_check_service_interface.h>

#include "chat.grpc.pb.h"
#include "chat.pb.h"

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;
using chat::Handler;
using chat::EnrollRequest;
using chat::EnrollResponse;
using chat::Empty;
using chat::Event;
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

class HandlerServiceImpl final : public Handler::Service {
    Status Enroll(ServerContext* context, const EnrollRequest* request,
                  EnrollResponse* response) override {
        participants_.insert(request->user());
        if (participants_.size() > 1) {
            n_event_ = GameStarted;
        }
        response->set_message("Hello, " + request->user());
        return Status::OK;
    }

    Status PollEvents(ServerContext* context, const Empty* request,
                  Event* response) override {
        response->set_n_event(n_event_);
        response->mutable_active()->CopyFrom({active_.begin(), active_.end()});
        response->mutable_players()->CopyFrom({participants_.begin(), participants_.end()});
        return Status::OK;
    }

    Status Vote (ServerContext* context, const VoteCandidate* request,
                 Empty* response) override {
        roles_sent_ = 0;
        votes_[request->name()]++;
        num_votes_++;
        if (num_votes_ == active_.size()) {
            std::string kicked;
            int max_votes = 0;
            for (const auto& p : votes_) {
                if (p.second > max_votes) {
                    max_votes = p.second;
                    kicked = p.first; 
                }
            }
            active_.erase(kicked);
            n_event_ = MafiaTurn;
            votes_.clear();
            num_votes_ = 0;
        }
        return Status::OK;
    }

    Status GetRole (ServerContext* context, const Username* request,
                    Role* response) override {
        roles_sent_++;
        if (mafia_.empty()) {
            response->set_role("Mafia");
            mafia_.insert(request->name());
        } else {
            if (comissars_.empty()) {
                response->set_role("Comissar");
                comissars_.insert(request->name());
            } else {
                response->set_role("Citizen");
            }
        }
        if (roles_sent_ >= participants_.size()) {
            n_event_ = Voting;
        }
        return Status::OK;
    }

private:
    std::set<std::string> participants_;
    std::set<std::string> active_;
    std::map<std::string, int> votes_;
    std::set<std::string> mafia_;
    std::set<std::string> comissars_;
    int num_votes_;
    int n_event_ = 0;
    int roles_sent_;
};

void RunServer() {
    std::string server_address("0.0.0.0:50051");
    HandlerServiceImpl service;

    grpc::EnableDefaultHealthCheckService(true);
    grpc::reflection::InitProtoReflectionServerBuilderPlugin();
    ServerBuilder builder;

    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());

    builder.RegisterService(&service);

    std::unique_ptr<Server> server(builder.BuildAndStart());
    std::cout << "Server listening on " << server_address << std::endl;

    server->Wait();
}

int main(int argc, char** argv) {
    RunServer();

    return 0;
}