import itertools
import random
from tools.string_tools import StringTools


class PretAVoterSpthyGenerator:
    spthy_model = ""

    def __init__(self, no_voters, no_candidates, single=True):
        self.no_voters = no_voters
        self.no_candidates = no_candidates
        self.single = single
        return

    def create_spthy_model(self):
        self.spthy_model += f"theory PretAVoterV{self.no_voters}C{self.no_candidates}\n"
        self.spthy_model += "begin\n\n"
        self.spthy_model += self.__define_builtins()
        self.spthy_model += self.__define_functions()
        self.spthy_model += self.__define_equations()
        self.spthy_model += self.__define_rules()
        self.spthy_model += self.__define_restrictions()
        self.spthy_model += self.__define_lemmas()

        self.spthy_model += "end\n"
        return self.spthy_model

    def __define_builtins(self):
        builtins = "builtins: "
        libraries = ['asymmetric-encryption', 'multiset']
        for lib in libraries:
            builtins += f'{lib}, '

        builtins = builtins.rstrip(' ,')
        builtins += '\n\n'
        return builtins

    def __define_functions(self):
        functions = "functions: select/2, s/1, z/0\n\n"
        return functions

    def __define_equations(self):
        equations = "equations:\n"
        candidate_list = self.__generate_candidate_list()
        candidate_list = candidate_list.rstrip(" ,")
        choice = "z"
        for candidate_id in range(1, self.no_candidates + 1):
            choice = f"s({choice})"
            equations += f"\tselect({choice}, <{candidate_list}>) = C{candidate_id}\n"
        equations += "\n"
        return equations

    def __define_rules(self):
        rules = ""

        rules += self.__define_setup_rules()
        rules += self.__define_ballot_generation_rule()
        rules += self.__define_vote_intruder_casting_rule()
        if self.single:
            rules += self.__define_single_vote_casting_rule()
            rules += self.__define_single_vote_publishing_rule()
            rules += self.__define_single_vote_counting_rule()
        else:
            rules += self.__define_votes_casting_rule()
            rules += self.__define_votes_publishing_rule()
            rules += self.__define_votes_counting_rule()
        rules += self.__define_vote_verifying_rule()

        return rules

    def __define_setup_rules(self):
        setup = ""
        setup += self.__define_initial_setup_rule()
        return setup

    def __define_initial_setup_rule(self):
        rule = "rule InitialSetup:\n"
        rule += '\t[\n'
        rule += '\t\tFr(~f)\n'
        rule += '\t]\n'
        rule += '  --[ InitialSetup(), RunOnce() ]->\n'
        rule += '\t[\n'

        rule += self.__generate_initial_voters()
        rule += self.__generate_initial_candidates()
        rule += self.__generate_initial_choices()
        rule += self.__generate_initial_ballots()
        rule += self.__generate_initial_election_authority()

        rule += '\t]\n'
        rule += '\n'
        return rule

    def __generate_initial_voters(self):
        facts = ""
        for voter_id in range(1, self.no_voters):
            facts += f"\t\tVoter($V{voter_id}),\n"
        facts += f"\t\tVoterI($V{self.no_voters}),\n"
        return facts

    def __generate_initial_candidates(self):
        facts = ""
        for candidate_id in range(1, self.no_candidates + 1):
            facts += f"\t\t!Candidate('C{candidate_id}'),\n"
        return facts

    def __generate_initial_choices(self):
        facts = ""
        choice = 'z'
        for _ in range(0, self.no_candidates):
            choice = f"s({choice})"
            facts += f"\t\t!Choice({choice}),\n"
        return facts

    def __generate_initial_ballots(self):
        facts = ""
        for ballot_id in range(1, self.no_voters + 1):
            facts += f"\t\tBallot($B{ballot_id}),\n"
        return facts

    def __generate_initial_election_authority(self):
        facts = ""
        facts += "\t\t!ElectionAuthority($E),\n"
        facts += "\t\t!Sk($E, ~f),\n"
        facts += "\t\t!Pk($E, pk(~f))\n"
        return facts

    def __define_ballot_generation_rule(self):
        rule = "rule GenerateBallot:\n"
        candidate_list = self.__generate_candidate_list()
        rule += "\tlet\n"
        rule += f"\t\tonion = aenc(<{candidate_list}, ~d>, pkE)\n"
        rule += f"\tin\n"
        rule += '\t[\n'
        rule += '\t\tBallot(B),\n'
        rule += self.__generate_candidates_facts()
        rule += '\t\t!ElectionAuthority(E),\n'
        rule += "\t\t!Pk(E, pkE),\n"
        rule += "\t\tFr(~d)\n"
        rule += '\t]\n'
        rule += f'  --[ GenerateBallot(B, {candidate_list}, onion), GenerateBallotR() ]->\n'
        rule += '\t[\n'
        rule += f"\t\tBallotWithOrderAndOnion(B, {candidate_list}, onion)\n"
        rule += '\t]\n'
        rule += '\n'
        return rule

    def __generate_candidates_facts(self):
        facts = ""
        for candidate_id in range(1, self.no_candidates + 1):
            facts += f"\t\t!Candidate(C{candidate_id}),\n"
        return facts

    def __generate_candidate_list(self, voter_id=0):
        candidate_list = ""
        for candidate_id in range(1, self.no_candidates + 1):
            if voter_id == 0:
                candidate_list += f"C{candidate_id}, "
            else:
                candidate_list += f"C{candidate_id}.{voter_id}, "
        return candidate_list.rstrip(" ,")

    def __define_single_vote_casting_rule(self):
        rule = "rule CastVote:\n"
        candidate_list = self.__generate_candidate_list()
        rule += '\t[\n'
        rule += '\t\t!Choice(c),\n'
        rule += '\t\tVoter(V),\n'
        rule += f"\t\tBallotWithOrderAndOnion(B, {candidate_list}, onion)\n"
        rule += '\t]\n'
        rule += f'  --[ CastVote(V, c, onion) ]->\n'
        rule += '\t[\n'
        rule += "\t\tVote(c, onion),\n"
        rule += "\t\tReceipt(V, c, onion)\n"
        rule += '\t]\n'
        rule += '\n'
        return rule

    def __define_votes_casting_rule(self):
        rule = "rule CastVotes:\n"

        rule += '\t[\n'
        for voter_id in range(1, self.no_voters):
            candidate_list = self.__generate_candidate_list(voter_id)
            rule += f'\t\t\\\\--Voter {voter_id}--\n'
            rule += f'\t\t!Choice(c{voter_id}),\n'
            rule += f'\t\tVoter(V{voter_id}),\n'
            rule += f"\t\tBallotWithOrderAndOnion(B{voter_id}, {candidate_list}, onion{voter_id})\n"
        rule += '\t]\n'
        rule += f'  --[ CastVotes() ]->\n'
        rule += '\t[\n'
        for voter_id in range(1, self.no_voters):
            rule += f'\t\t\\\\--Voter {voter_id}--\n'
            rule += f"\t\tVote(c{voter_id}, onion{voter_id}),\n"
            rule += f"\t\tReceipt(V{voter_id}, c{voter_id}, onion{voter_id})\n"
        rule += '\t]\n'
        rule += '\n'
        return rule

    def __define_vote_intruder_casting_rule(self):
        rule = "\\\\ Vote casted by coerced voter\n"
        rule += "rule CastVoteI:\n"
        candidate_list = self.__generate_candidate_list()
        rule += "\tlet\n"
        rule += f"\t\tch = diff(ch1, ch2)\n"
        rule += f"\tin\n"
        rule += '\t[\n'
        rule += "\t\t\\\\ Candidate selected by Intruder\n"
        rule += "\t\tIn(ic),\n"
        rule += '\t\t!Choice(ch1),\n'
        rule += '\t\t!Choice(ch2),\n'
        rule += '\t\tVoterI(V),\n'
        rule += f"\t\tBallotWithOrderAndOnion(B, {candidate_list}, onion)\n"
        rule += '\t]\n'
        rule += f'  --[ CastVote(V, c, onion), Eq(select(ch2, <{candidate_list}>), ic), IntruderCandidate(ic) ]->\n'
        rule += '\t[\n'
        rule += "\t\tVote(c, onion),\n"
        rule += "\t\tReceipt(V, c, onion),\n"
        rule += "\t\t\\\\ Share vote receipt with Intruder\n"
        rule += "\t\tOut(<V, c, onion>)\n"
        rule += '\t]\n'
        rule += '\n'
        return rule

    def __define_single_vote_publishing_rule(self):
        rule = "rule PublishVote:\n"
        rule += '\t[\n'
        rule += "\t\tVote(c, onion)\n"
        rule += '\t]\n'
        rule += f'  --[ PublishVote(c, onion) ]->\n'
        rule += '\t[\n'
        rule += "\t\tVoteToCount(c, onion),\n"
        rule += "\t\t!Board(c, onion)\n"
        rule += '\t]\n'
        rule += '\n'
        return rule

    def __define_votes_publishing_rule(self):
        rule = "rule PublishVotes:\n"
        rule += '\t[\n'
        for voter_id in range(1, self.no_voters + 1):
            rule += f"\t\tVote(c{voter_id}, onion{voter_id}),\n"
        rule = rule.rstrip("\n,")
        rule += "\n"
        rule += '\t]\n'
        rule += f'  --[ PublishVotes() ]->\n'
        rule += '\t[\n'
        for voter_id in range(1, self.no_voters + 1):
            rule += f"\t\tVoteToCount(c{voter_id}, onion{voter_id}),\n"
            rule += f"\t\t!Board(c{voter_id}, onion{voter_id}),\n"
        rule += "\t\tOut("
        for voter_id in range(1, self.no_voters + 1):
            rule += f"<c{voter_id}, onion{voter_id}> + "
        rule = rule.rstrip(" +")
        rule += ")\n"
        rule += '\t]\n'
        rule += '\n'
        return rule

    def __define_single_vote_counting_rule(self):
        rule = "rule CountVote:\n"
        candidate_list = self.__generate_candidate_list()
        rule += "\tlet\n"
        rule += f"\t\tonion = aenc(<{candidate_list}, ~d>, pkE)\n"
        rule += f"\t\tchosen = select(selection, <{candidate_list}>)\n"
        rule += f"\tin\n"
        rule += '\t[\n'
        rule += "\t\t!ElectionAuthority(E),\n"
        rule += "\t\t!Sk(E, skE),\n"
        rule += "\t\tVoteToCount(selection, onion)\n"
        rule += '\t]\n'
        rule += f'  --[ CountVote(chosen) ]->\n'
        rule += '\t[\n'
        rule += "\t\tDecBoard(chosen)\n"
        rule += '\t]\n'
        rule += '\n'
        return rule

    def __define_votes_counting_rule(self):
        rule = "rule CountVotes:\n"
        rule += "\tlet\n"
        for voter_id in range(1, self.no_voters + 1):
            candidate_list = self.__generate_candidate_list(voter_id)
            rule += f"\t\tonion{voter_id} = aenc(<{candidate_list}, ~d.{voter_id}>, pkE)\n"
            rule += f"\t\tchosen{voter_id} = select(selection{voter_id}, <{candidate_list}>)\n"
        rule += f"\tin\n"
        rule += '\t[\n'
        for voter_id in range(1, self.no_voters + 1):
            rule += f"\t\tVoteToCount(selection{voter_id}, onion{voter_id}),\n"
        rule += "\t\t!ElectionAuthority(E),\n"
        rule += "\t\t!Sk(E, skE)\n"
        rule += '\t]\n'
        rule += f'  --[ CountVotes() ]->\n'
        rule += '\t[\n'
        for voter_id in range(1, self.no_voters + 1):
            rule += f"\t\tDecBoard(chosen{voter_id}),\n"
        rule += "\t\tOut("
        for voter_id in range(1, self.no_voters + 1):
            rule += f"chosen{voter_id} + "
        rule = rule.rstrip(" +")
        rule += ")\n"
        rule += '\t]\n'
        rule += '\n'
        return rule

    def __define_vote_verifying_rule(self):
        rule = "rule VerifyVote:\n"
        rule += '\t[\n'
        rule += '\t\tReceipt(V, selection, onion),\n'
        rule += '\t\t!Board(selection, onion),\n'
        rule += '\t]\n'
        rule += f'  --[ VerifyVote(V, selection, onion) ]->\n'
        rule += '\t[\n'
        rule += '\t]\n'
        rule += '\n'
        return rule

    def __define_restrictions(self):
        restrictions = ""
        restrictions += "restriction RunInitialSetupOnce:\n"
        restrictions += '\t"All #i1 #i2. RunOnce() @i1 & RunOnce() @i2 ==> #i1=#i2"\n\n'
        restrictions += 'restriction Unique:\n'
        cand_list = ""
        for candidate_id in range(1, self.no_candidates + 1):
            cand_list += f"C{candidate_id} "
        eq = ""
        for candidate_id_1 in range(1, self.no_candidates):
            for candidate_id_2 in range(candidate_id_1 + 1, self.no_candidates + 1):
                eq += f"not(C{candidate_id_1}=C{candidate_id_2}) & "
        eq = eq.rstrip(" &")
        restrictions += f'\t"All B {cand_list}onion #i. GenerateBallot(B, {self.__generate_candidate_list()}, onion) @i ==> ({eq})"\n\n'
        restrictions += 'restriction Equality:\n'
        restrictions += '\t"All x y #i. Eq(x,y) @i ==> x = y"\n\n'
        return restrictions

    def __define_lemmas(self):
        lemmas = ""
        for candidate_id in range(1, self.no_candidates + 1):
            lemmas += f"lemma IntruderStrategyC{candidate_id}:\n"
            lemmas += f'\t"All V C #i.\n'
            lemmas += f"\t\tIntruderCandidate('C{candidate_id}') @ #i ==>\n"
            lemmas += f'\t\t\tEx #j. K(<V, C>) @ #j\n'
            lemmas += '\t"\n\n'

        return lemmas


voters_no = 4
candidates_no = 3
pret_a_voter_spthy_generator = PretAVoterSpthyGenerator(voters_no, candidates_no, False)
file_name = f"pret_a_voter_v{voters_no}_c{candidates_no}.spthy"
f = open(file_name, "w")
f.write(pret_a_voter_spthy_generator.create_spthy_model())
f.close()

print(f"Done. Created model saved in {file_name}")
