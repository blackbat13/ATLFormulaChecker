import itertools
import random


class SeleneModelIsplGenerator:
    ispl_model = ""

    def __init__(self, number_of_candidates, number_of_voters):
        self.number_of_candidates = number_of_candidates
        self.number_of_voters = number_of_voters

    def create_ispl_model(self):
        self.ispl_model += "Semantics = SA;\n"
        self.ispl_model += self.__create_environment()
        self.ispl_model += self.__create_coercer()
        for voter_number in range(1, self.number_of_voters + 1):
            self.ispl_model += self.__create_voter(voter_number)
        self.ispl_model += self.__create_evaluation()
        self.ispl_model += self.__create_init_states()
        self.ispl_model += self.__create_groups()
        self.ispl_model += self.__create_formulae()
        return self.ispl_model

    def __create_environment(self):
        environment = "Agent Environment\n"
        environment += self.__create_environment_obsvars()
        environment += self.__create_environment_vars()
        environment += self.__create_environment_actions()
        environment += self.__create_environment_protocol()
        environment += self.__create_environment_evolution()
        environment += "end Agent\n\n"
        return environment

    def __create_environment_obsvars(self):
        obsvars = "\tObsvars:\n"

        for i in range(1, self.number_of_voters + 1):
            obsvars += "\t\tpublicTracker" + str(i) + ": 0.." + str(self.number_of_voters) + ";\n"
            obsvars += "\t\tpublicVote" + str(i) + ": 0.." + str(self.number_of_candidates) + ";\n"

        obsvars += "\t\tvotesPublished: boolean;\n"
        obsvars += "\t\tvotingStarted: boolean;\n"
        obsvars += "\tend Obsvars\n"
        return obsvars

    def __create_environment_vars(self):
        vars = "\tVars:\n"

        for i in range(1, self.number_of_voters+1):
            vars += "\t\ttracker" + str(i) + ": 0.." + str(self.number_of_voters) + ";\n"
            vars += "\t\tvoter" + str(i) + "Voted: boolean;\n"
            vars += "\t\tvoter" + str(i) + "Vote: 0.." + str(self.number_of_candidates) + ";\n"
            vars += "\t\tvoter" + str(i) + "TrackerSet: boolean;\n"
            vars += "\t\tvoter" + str(i) + "OwnedTracker: 0.." + str(self.number_of_voters) + ";\n"

        vars += "\tend Vars\n"
        return vars

    def __create_environment_actions(self):
        actions = "\tActions = {PublishVotes, "
        for i in range(1, self.number_of_voters + 1):
            for j in range(1, self.number_of_voters + 1):
                actions += "SetTracker" + str(i) + "To" + str(j) + ", "
        actions += "StartVoting, Wait};\n"
        return actions

    def __create_environment_protocol(self):
        protocol = "\tProtocol:\n"

        protocol += "\t\t"
        for i in range(1, self.number_of_voters + 1):
            protocol += "voter" + str(i) + "Voted=true and "

        protocol += "publicVote1=0: {PublishVotes};\n"

        for i in range(1, self.number_of_voters + 1):
            for j in range(1, self.number_of_voters + 1):
                protocol += "\t\ttracker" + str(i) + "=0 and voter" + str(j) + "TrackerSet=false: {SetTracker" + str(i) + "To" + str(j) + "};\n"

        protocol += "\t\t"
        for i in range(1, self.number_of_voters + 1):
            protocol += "tracker" + str(i) + ">0 and "

        protocol += "votingStarted=false: {StartVoting};\n"
        protocol += "\t\tOther: {Wait};\n"
        protocol += "\tend Protocol\n"
        return protocol

    def __create_environment_evolution(self):
        evolution = "\tEvolution:\n"

        for i in range(1, self.number_of_voters + 1):
            for j in range(1, self.number_of_voters + 1):
                evolution += "\t\tpublicTracker" + str(i) + "=" + str(j) + " if\n"
                evolution += "\t\t\tAction=PublishVotes and\n"
                evolution += "\t\t\ttracker" + str(i) + "=" + str(j) + ";\n"

        for i in range(1, self.number_of_voters + 1):
            for j in range(1, self.number_of_candidates + 1):
                for k in range(1, self.number_of_voters + 1):
                    evolution += "\t\tpublicVote" + str(i) + "=" + str(j) + " if\n"
                    evolution += "\t\t\tAction=PublishVotes and\n"
                    evolution += "\t\t\tvoter" + str(k) + "Vote=" + str(j) + " and\n"
                    evolution += "\t\t\ttracker" + str(i) + "=" + str(k) + ";\n"

        for voter_number in range(1, self.number_of_voters + 1):
            evolution += "\t\tvoter" + str(voter_number) + "Voted=true if\n"
            for candidate_number in range(1, self.number_of_candidates+1):
                evolution += "\t\t\tVoter" + str(voter_number) + ".Action=Vote" + str(candidate_number) + " or\n"
            evolution = evolution.rstrip("\nro ")
            evolution += ";\n"

        for i in range(1, self.number_of_voters + 1):
            for j in range(1, self.number_of_candidates + 1):
                evolution += "\t\tvoter" + str(i) + "Vote=" + str(j) + " if\n"
                evolution += "\t\t\tVoter" + str(i) + ".Action=Vote" + str(j) + ";\n"

        for i in range(1, self.number_of_voters + 1):
            evolution += "\t\tvoter" + str(i) + "TrackerSet=true if\n"
            for j in range(1, self.number_of_voters + 1):
                evolution += "\t\t\tAction=SetTracker" + str(j) + "To" + str(i) + " or\n"
            evolution = evolution.rstrip("\nro ")
            evolution += ";\n"

        for i in range(1, self.number_of_voters + 1):
            for j in range(1, self.number_of_voters + 1):
                evolution += "\t\ttracker" + str(i) + "=" + str(j) + " if\n"
                evolution += "\t\t\tAction=SetTracker" + str(i) + "To" + str(j) + ";\n"

        for i in range(1, self.number_of_voters + 1):
            for j in range(1, self.number_of_voters + 1):
                evolution += "\t\tvoter" + str(i) + "OwnedTracker=" + str(j) + " if\n"
                evolution += "\t\t\tVoter" + str(i) + ".Action=FetchGoodTracker and "
                evolution += "tracker" + str(j) + "=" + str(i) + ";\n"

        for i in range(1, self.number_of_voters + 1):
            for j in range(1, self.number_of_voters + 1):
                for l in range(1, self.number_of_voters + 1):
                    for k in range(1, self.number_of_candidates + 1):
                        evolution += "\t\tvoter" + str(i) + "OwnedTracker=" + str(j) + " if\n"
                        evolution += "\t\t\tVoter" + str(i) + ".Action=FetchTrackerForVote" + str(k) + " and "
                        evolution += "voter" + str(l) + "Vote=" + str(k) + " and "
                        evolution += "tracker" + str(j) + "=" + str(l) + ";\n"

        evolution += "\t\tvotesPublished=true if Action=PublishVotes;\n"
        evolution += "\t\tvotingStarted=true if Action=StartVoting;\n"

        evolution += "\tend Evolution\n"
        return evolution

    def __create_coercer(self):
        player = "Agent Coercer\n"

        player += self.__create_coercer_lobsvars()
        player += self.__create_coercer_vars()
        player += self.__create_coercer_actions()
        player += self.__create_coercer_protocol()
        player += self.__create_coercer_evolution()
        player += "end Agent\n\n"
        return player

    def __create_coercer_lobsvars(self):
        lobsvars = "\tLobsvars = {"

        lobsvars += "};\n"
        return lobsvars

    def __create_coercer_vars(self):
        vars = "\tVars:\n"
        for i in range(1, self.number_of_voters + 1):
            vars += '\t\ttracker' + str(i) + ": 0.." + str(self.number_of_voters) + ";\n"
        vars += "\tend Vars\n"
        return vars

    def __create_coercer_actions(self):
        actions = "\tActions = {"

        actions += "Wait};\n"
        return actions

    def __create_coercer_protocol(self):
        protocol = "\tProtocol:\n"
        protocol += "\t\tEnvironment.votesPublished=false: {Wait};\n"
        protocol += "\tend Protocol\n"
        return protocol

    def __create_coercer_evolution(self, ):
        evolution = "\tEvolution:\n"

        evolution += "\tend Evolution\n"
        return evolution

    def __create_voter(self, voter_number):
        player = "Agent Voter" + str(voter_number) + "\n"

        player += self.__create_voter_lobsvars(voter_number)
        player += self.__create_voter_vars()
        player += self.__create_voter_actions()
        player += self.__create_voter_protocol(voter_number)
        player += self.__create_voter_evolution()
        player += "end Agent\n\n"
        return player

    def __create_voter_lobsvars(self, voter_number):
        lobsvars = "\tLobsvars = {"
        lobsvars += "voter" + str(voter_number) + "OwnedTracker"
        lobsvars += "};\n"
        return lobsvars

    def __create_voter_vars(self):
        vars = "\tVars:\n"

        vars += "\t\tvote: 0.." + str(self.number_of_candidates) + ";\n"

        vars += "\tend Vars\n"
        return vars

    def __create_voter_actions(self):
        actions = "\tActions = {"

        for i in range(1, self.number_of_candidates + 1):
            actions += "Vote" + str(i) + ", "

        for i in range(1, self.number_of_candidates + 1):
            actions += "FetchTrackerForVote" + str(i) + ", "

        actions += "FetchGoodTracker, "
        actions += "Wait};\n"
        return actions

    def __create_voter_protocol(self, voter_number):
        protocol = "\tProtocol:\n"

        protocol += "\t\tvote=0 and Environment.votingStarted=true: {"
        for i in range(1, self.number_of_candidates + 1):
            protocol += "Vote" + str(i) + ", "

        protocol += "Wait};\n"

        protocol += "\t\tvote>0 and Environment.voter" + str(voter_number) + "OwnedTracker=0 and Environment.votesPublished=true: {"
        for i in range(1, self.number_of_candidates + 1):
            protocol += "FetchTrackerForVote" + str(i) + ", "
        protocol += "FetchGoodTracker, Wait};\n"
        protocol += "\t\tOther: {Wait};\n"

        protocol += "\tend Protocol\n"
        return protocol

    def __create_voter_evolution(self, ):
        evolution = "\tEvolution:\n"

        for i in range(1, self.number_of_candidates + 1):
            evolution += "\t\tvote=" + str(i) + " if Action=Vote" + str(i) + ";\n"

        evolution += "\tend Evolution\n"
        return evolution

    def __create_evaluation(self):
        evaulation = "Evaluation\n"
        evaulation += "\tVoter1Voted1 if Voter1.vote=1;\n"
        evaulation += "end Evaluation\n\n"
        return evaulation

    def __create_init_states(self):
        init_states = "InitStates\n"
        init_states += "\t\t"
        # Set trackers to voter number
        for i in range(1, self.number_of_voters + 1):
            init_states += "Voter" + str(i) + ".vote=0 and "
            init_states += "Environment.publicTracker" + str(i) + "=0 and "
            init_states += "Environment.publicVote" + str(i) + "=0 and "
            init_states += "Environment.tracker" + str(i) + "=" + str(0) + " and "
            init_states += "Environment.voter" + str(i) + "Voted=false and "
            init_states += "Environment.voter" + str(i) + "Vote=0 and "
            init_states += "Environment.voter" + str(i) + "TrackerSet=false and "
            init_states += "Environment.voter" + str(i) + "OwnedTracker=0 and "
            init_states += "Coercer.tracker" + str(i) + "=0 and"

        init_states += "Environment.votesPublished=false and "
        init_states += "Environment.votingStarted=false"
        init_states += ";\n"
        init_states += "end InitStates\n\n"
        return init_states

    def __create_groups(self):
        groups = "Groups\n"
        for voter_number in range(1, self.number_of_voters + 1):
            groups += "\tv" + str(voter_number) + "={Voter" + str(voter_number) + "};\n"
        groups += "end Groups\n\n"
        return groups

    def __create_formulae(self):
        formulae = "Formulae\n"
        formulae += "\t<v1>F(Voter1Voted1);\n"
        formulae += "end Formulae\n\n"
        return formulae


n = int(input("Number of candidates ="))
k = int(input("Number of voters ="))

selene_model_ispl_generator = SeleneModelIsplGenerator(n, k)
f = open("selene_" + str(n) + "_" + str(k) + ".ispl", "w")
f.write(selene_model_ispl_generator.create_ispl_model())
f.close()

print("Generated model saved in file selene_" + str(n) + "_" + str(k) + ".ispl")