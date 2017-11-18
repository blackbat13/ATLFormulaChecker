import itertools
import random


class BridgeModelIsplGenerator:
    card_names = ["Ace", "King", "Queen", "Jack", "ten", "nine", "eight", "seven", "six", "five", "four", "three",
                  "two"]
    card_colors = ["Spade", "Heart", "Diamond", "Club"]
    player_names = ["SPlayer", "WPlayer", "NPlayer", "EPlayer"]
    ispl_model = ""
    cards = []
    available_cards = []
    cards_values = {}
    cards_colors = {}

    def __init__(self, number_of_cards, number_of_cards_in_hand, card_ordering):
        self.number_of_cards = number_of_cards
        self.number_of_cards_in_hand = number_of_cards_in_hand
        self.card_ordering = card_ordering
        self.__create_cards_array()
        self.__create_available_cards_array()
        self.__assign_cards_values()
        self.__assign_cards_colors()

    def __create_cards_array(self):
        self.cards = []
        for card_name in self.card_names:
            for card_color in self.card_colors:
                self.cards.append(card_name + card_color)

    def __create_available_cards_array(self):
        self.available_cards = []
        for j in range(0, 4 * self.number_of_cards):
            self.available_cards.append(self.cards[j])

    def __assign_cards_values(self):
        i = 0
        for card_value in range(0, 13):
            for j in range(0, 4):
                self.cards_values[self.cards[i]] = 13 - card_value
                i += 1

    def __assign_cards_colors(self):
        i = 0
        for _ in range(0, 13):
            for color in self.card_colors:
                self.cards_colors[self.cards[i]] = color
                i += 1

    def create_ispl_model(self):
        self.ispl_model += self.__create_environment()
        self.ispl_model += self.__create_player(0)
        self.ispl_model += self.__create_player(1)
        self.ispl_model += self.__create_player(3)

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
        obsvars += "\t\tfirstTeamScore: 0.." + str(self.number_of_cards_in_hand) + ";\n"
        obsvars += "\t\tsecondTeamScore: 0.." + str(self.number_of_cards_in_hand) + ";\n"
        obsvars += "\t\tbeginningPlayer: 0..3;\n"
        obsvars += "\t\tcurrentPlayer: 0..4;\n"
        obsvars += "\t\tclock: 0..5;\n"

        obsvars += "\t\t" + self.player_names[0] + "Card: {"
        for j in range(0, 4 * self.number_of_cards):
            obsvars += self.cards[j] + ", "
        obsvars += "None};\n"

        for i in range(1, self.number_of_cards_in_hand + 1):
            obsvars += "\t\tcardN" + str(i) + ": {"
            for j in range(0, 4 * self.number_of_cards):
                obsvars += self.cards[j] + ", "
            obsvars += "None};\n"

        for i in range(0, self.number_of_cards * 4):
            obsvars += "\t\t" + self.cards[i] + "H: boolean;\n"

        obsvars += "\tend Obsvars\n"
        return obsvars

    def __create_environment_vars(self):
        vars = "\tVars:\n"
        for player in self.player_names:
            if player == self.player_names[0]:
                continue
            vars += "\t\t" + player + "Card: {"
            for j in range(0, 4 * self.number_of_cards):
                vars += self.cards[j] + ", "
            vars += "None};\n"

        for i in range(1, self.number_of_cards_in_hand + 1):
            vars += "\t\tcurrentCardN" + str(i) + ": {"
            for j in range(0, 4 * self.number_of_cards):
                vars += self.cards[j] + ", "
            vars += "None};\n"

        vars += "\t\tsuit: {Spade, Heart, Diamond, Club, None};\n"

        vars += "\tend Vars\n"
        return vars

    def __create_environment_actions(self):
        actions = "\tActions = {none};\n"
        return actions

    def __create_environment_protocol(self):
        protocol = "\tProtocol:\n\t\tOther:{none};\n\tend Protocol\n"
        return protocol

    def __create_environment_evolution(self):
        evolution = "\tEvolution:\n"

        for winning_player in range(0, 4):
            if winning_player % 2 == 0:
                evolution += "\t\tfirstTeamScore=firstTeamScore+1"
            else:
                evolution += "\t\tsecondTeamScore=secondTeamScore+1"

            evolution += " and beginningPlayer=" + str(
                winning_player) + " and clock=0 and suit=None and currentPlayer=" + str(
                winning_player)

            for player in self.player_names:
                evolution += " and " + player + "Card=None"

            for j in range(1, self.number_of_cards_in_hand + 1):
                evolution += " and cardN" + str(j) + "=currentCardN" + str(j)

            evolution += " if\n"
            add_or = False
            for combination in itertools.permutations(self.available_cards, 4):
                for beginning_player in range(0, 4):
                    winning_player_number = beginning_player
                    for i in range(0, 4):
                        if i == beginning_player:
                            continue

                        if self.cards_colors[combination[i]] == self.cards_colors[
                            combination[winning_player_number]]:
                            if self.cards_values[combination[i]] > self.cards_values[
                                combination[winning_player_number]]:
                                winning_player_number = i

                    if not (winning_player_number == winning_player):
                        continue

                    if add_or:
                        evolution += " or\n"
                    else:
                        add_or = True

                    evolution += "\t\t\t("
                    for player in range(0, 4):
                        evolution += self.player_names[player] + "Card=" + combination[player] + " and "

                    evolution += "beginningPlayer=" + str(beginning_player)
                    evolution += " and clock>=4)"

            evolution += ";\n"

        # for i in range(0, self.number_of_cards * 4):
        #     card = self.cards[i]
        #     for player_number in range(0, 4):
        #         if (player_number - 1) % 4 != 2:
        #             evolution += "\t\tclock=clock+1 and currentPlayer=" + str(
        #                 player_number) + " and " + self.player_names[
        #                              (player_number - 1) % 4] + "Card=" + card + " and " + card + "H=true if\n"
        #             evolution += "\t\t\t" + self.player_names[
        #                 (player_number - 1) % 4] + ".Action=Play" + card + " and currentPlayer=" + str(
        #                 (player_number - 1) % 4) + " and clock>0;\n"
        #
        #             evolution += "\t\tclock=clock+1 and currentPlayer=" + str(
        #                 player_number) + " and " + self.player_names[
        #                              (player_number - 1) % 4] + "Card=" + card + " and " + card + "H=true and suit=" + \
        #                          self.cards_colors[card] + " if\n"
        #             evolution += "\t\t\t" + self.player_names[
        #                 (player_number - 1) % 4] + ".Action=Play" + card + " and currentPlayer=" + str(
        #                 (player_number - 1) % 4) + " and clock=0;\n"
        #         else:
        #             for j in range(1, self.number_of_cards_in_hand + 1):
        #                 evolution += "\t\tclock=clock+1 and currentCardN" + str(j) + "=None and has"+ self.cards_colors[card] +"=has"+self.cards_colors[card]+"-1 and currentPlayer=" + str(
        #                     player_number) + " and " + self.player_names[
        #                                  (player_number - 1) % 4] + "Card=" + card + " and " + card + "H=true if\n"
        #                 evolution += "\t\t\t" + self.player_names[
        #                     0] + ".Action=Play" + card + " and currentPlayer=" + str(
        #                     (player_number - 1) % 4) + " and currentCardN" + str(j) + "=" + card + " and clock>0;\n"
        #
        #                 evolution += "\t\tclock=clock+1 and currentCardN" + str(j) + "=None and has"+ self.cards_colors[card] +"=has"+self.cards_colors[card]+"-1 and currentPlayer=" + str(
        #                     player_number) + " and " + self.player_names[
        #                                  (player_number - 1) % 4] + "Card=" + card + " and " + card + "H=true and suit=" + self.cards_colors[card] + " if\n"
        #                 evolution += "\t\t\t" + self.player_names[
        #                     0] + ".Action=Play" + card + " and currentPlayer=" + str(
        #                     (player_number - 1) % 4) + " and currentCardN" + str(j) + "=" + card + " and clock=0;\n"

        for i in range(0, self.number_of_cards * 4):
            card = self.cards[i]

            # Player S plays
            evolution += "\t\tcurrentPlayer=1 and clock=clock+1 and SPlayerCard=" + card + " and " + card + "H=true"
            evolution += " if\n"
            evolution += "\t\t\tcurrentPlayer=0 and clock<4 and clock>0 and SPlayer.Action=Play" + card + ";\n"

            evolution += "\t\tcurrentPlayer=1 and clock=clock+1 and SPlayerCard=" + card + " and " + card + "H=true"
            evolution += " and suit=" + self.cards_colors[card]
            evolution += " if\n"
            evolution += "\t\t\tcurrentPlayer=0 and clock<4 and clock=0 and SPlayer.Action=Play" + card + ";\n"

            # Player S should play, but play Player N card

            for j in range(1, self.number_of_cards_in_hand + 1):
                evolution += "\t\tNPlayerCard=" + card + " and " + card + "H=true and currentCardN" + str(j) + "=None"
                evolution += " if\n"
                evolution += "\t\t\tcurrentPlayer=0 and clock<4 and SPlayer.Action=PlayN" + card + " and currentCardN" + str(
                    j) + "=" + card + " and NPlayerCard=None;\n"

            # Player W plays, Player S Wait

            evolution += "\t\tcurrentPlayer=2 and clock=clock+1 and WPlayerCard=" + card + " and " + card + "H=true"
            evolution += " if\n"
            evolution += "\t\t\tcurrentPlayer=1 and clock>0 and WPlayer.Action=Play" + card + " and SPlayer.Action=Wait and NPlayerCard=None;\n"

            evolution += "\t\tcurrentPlayer=2 and clock=clock+1 and WPlayerCard=" + card + " and " + card + "H=true"
            evolution += " and suit=" + self.cards_colors[card]
            evolution += " if\n"
            evolution += "\t\t\tcurrentPlayer=1 and clock=0 and WPlayer.Action=Play" + card + " and SPlayer.Action=Wait and NPlayerCard=None;\n"

            evolution += "\t\tcurrentPlayer=3 and clock=clock+2 and WPlayerCard=" + card + " and " + card + "H=true"
            evolution += " if\n"
            evolution += "\t\t\tcurrentPlayer=1 and clock>0 and WPlayer.Action=Play" + card + " and SPlayer.Action=Wait and !(NPlayerCard=None);\n"

            evolution += "\t\tcurrentPlayer=3 and clock=clock+2 and WPlayerCard=" + card + " and " + card + "H=true"
            evolution += " and suit=" + self.cards_colors[card]
            evolution += " if\n"
            evolution += "\t\t\tcurrentPlayer=1 and clock=0 and WPlayer.Action=Play" + card + " and SPlayer.Action=Wait and !(NPlayerCard=None);\n"

            # Player W plays, Player S Play his card
            for i2 in range(0, self.number_of_cards * 4):
                card2 = self.cards[i2]

                if card == card2:
                    continue

                evolution += "\t\tcurrentPlayer=2 and clock=clock+1 and WPlayerCard=" + card + " and " + card + "H=true"
                evolution += " and SPlayerCard=" + card2 + " and " + card2 + "H=true"
                evolution += " and suit=" + self.cards_colors[card]
                evolution += " if\n"
                evolution += "\t\t\tcurrentPlayer=1 and clock=0 and WPlayer.Action=Play" + card + " and SPlayer.Action=Play" + card2 + " and NPlayerCard=None;\n"

                evolution += "\t\tcurrentPlayer=3 and clock=clock+2 and WPlayerCard=" + card + " and " + card + "H=true"
                evolution += " and SPlayerCard=" + card2 + " and " + card2 + "H=true"
                evolution += " and suit=" + self.cards_colors[card]
                evolution += " if\n"
                evolution += "\t\t\tcurrentPlayer=1 and clock=0 and WPlayer.Action=Play" + card + " and SPlayer.Action=Play" + card2 + " and !(NPlayerCard=None);\n"

            # Player W plays, Player S Play N card
            for i2 in range(0, self.number_of_cards * 4):
                card2 = self.cards[i2]
                if card == card2:
                    continue

                for j in range(1, self.number_of_cards_in_hand + 1):
                    evolution += "\t\tcurrentPlayer=3 and clock=clock+2 and WPlayerCard=" + card + " and " + card + "H=true"
                    evolution += " and NPlayerCard=" + card2 + " and " + card2 + "H=true"
                    evolution += " and currentCardN" + str(j) + "=None"
                    evolution += " if\n"
                    evolution += "\t\t\tcurrentPlayer=1 and clock>0 and WPlayer.Action=Play" + card + " and SPlayer.Action=PlayN" + card2 + " and NPlayerCard=None"
                    evolution += " and currentCardN" + str(j) + "=" + card2
                    evolution += ";\n"

                    evolution += "\t\tcurrentPlayer=3 and clock=clock+2 and WPlayerCard=" + card + " and " + card + "H=true"
                    evolution += " and NPlayerCard=" + card2 + " and " + card2 + "H=true"
                    evolution += " and currentCardN" + str(j) + "=None"
                    evolution += " and suit=" + self.cards_colors[card]
                    evolution += " if\n"
                    evolution += "\t\t\tcurrentPlayer=1 and clock=0 and WPlayer.Action=Play" + card + " and SPlayer.Action=PlayN" + card2 + " and NPlayerCard=None"
                    evolution += " and currentCardN" + str(j) + "=" + card2
                    evolution += ";\n"

                evolution += "\t\tcurrentPlayer=3 and clock=clock+2 and WPlayerCard=" + card + " and " + card + "H=true"
                evolution += " if\n"
                evolution += "\t\t\tcurrentPlayer=1 and clock>0 and WPlayer.Action=Play" + card + " and SPlayer.Action=PlayN" + card2 + " and !(NPlayerCard=None)"
                evolution += ";\n"

                evolution += "\t\tcurrentPlayer=3 and clock=clock+2 and WPlayerCard=" + card + " and " + card + "H=true"
                evolution += " and suit=" + self.cards_colors[card]
                evolution += " if\n"
                evolution += "\t\t\tcurrentPlayer=1 and clock=0 and WPlayer.Action=Play" + card + " and SPlayer.Action=PlayN" + card2 + " and !(NPlayerCard=None)"
                evolution += ";\n"

            # Player N Plays

            for j in range(1, self.number_of_cards_in_hand + 1):
                evolution += "\t\tcurrentPlayer=3 and clock=clock+1 and NPlayerCard=" + card + " and " + card + "H=true and currentCardN" + str(
                    j) + "=None"
                evolution += " if\n"
                evolution += "\t\t\tcurrentPlayer=2 and clock>0 and clock<4 and SPlayer.Action=PlayN" + card + " and currentCardN" + str(
                    j) + "=" + card + " and NPlayerCard=None;\n"

                evolution += "\t\tcurrentPlayer=3 and clock=clock+1 and NPlayerCard=" + card + " and " + card + "H=true and currentCardN" + str(
                    j) + "=None"
                evolution += " and suit=" + self.cards_colors[card]
                evolution += " if\n"
                evolution += "\t\t\tcurrentPlayer=2 and clock=0 and SPlayer.Action=PlayN" + card + " and currentCardN" + str(
                    j) + "=" + card + " and NPlayerCard=None;\n"

            # Player N should Play, Player S play his own card

            evolution += "\t\tSPlayerCard=" + card + " and " + card + "H=true"
            evolution += " if\n"
            evolution += "\t\t\tcurrentPlayer=2 and clock<4 and SPlayer.Action=Play" + card + ";\n"

            # Player E Plays, Player S Wait

            evolution += "\t\tcurrentPlayer=0 and clock=clock+1 and EPlayerCard=" + card + " and " + card + "H=true"
            evolution += " if\n"
            evolution += "\t\t\tcurrentPlayer=3 and clock>0 and EPlayer.Action=Play" + card + " and SPlayer.Action=Wait and SPlayerCard=None;\n"

            evolution += "\t\tcurrentPlayer=0 and clock=clock+1 and EPlayerCard=" + card + " and " + card + "H=true"
            evolution += " and suit=" + self.cards_colors[card]
            evolution += " if\n"
            evolution += "\t\t\tcurrentPlayer=3 and clock=0 and EPlayer.Action=Play" + card + " and SPlayer.Action=Wait and SPlayerCard=None;\n"

            evolution += "\t\tcurrentPlayer=1 and clock=clock+2 and EPlayerCard=" + card + " and " + card + "H=true"
            evolution += " if\n"
            evolution += "\t\t\tcurrentPlayer=3 and clock>0 and EPlayer.Action=Play" + card + " and SPlayer.Action=Wait and !(SPlayerCard=None);\n"

            evolution += "\t\tcurrentPlayer=1 and clock=clock+2 and EPlayerCard=" + card + " and " + card + "H=true"
            evolution += " and suit=" + self.cards_colors[card]
            evolution += " if\n"
            evolution += "\t\t\tcurrentPlayer=3 and clock=0 and EPlayer.Action=Play" + card + " and SPlayer.Action=Wait and !(SPlayerCard=None);\n"

            # Player E Plays, Player S Play his card

            for i2 in range(0, self.number_of_cards * 4):
                card2 = self.cards[i2]

                if card == card2:
                    continue

                evolution += "\t\tcurrentPlayer=1 and clock=clock+2 and EPlayerCard=" + card + " and " + card + "H=true"
                evolution += " and SPlayerCard=" + card2 + " and " + card2 + "H=true"
                evolution += " and suit=" + self.cards_colors[card]
                evolution += " if\n"
                evolution += "\t\t\tcurrentPlayer=3 and clock=0 and EPlayer.Action=Play" + card + " and SPlayer.Action=Play" + card2 + ";\n"

                evolution += "\t\tcurrentPlayer=1 and clock=clock+2 and EPlayerCard=" + card + " and " + card + "H=true"
                evolution += " and SPlayerCard=" + card2 + " and " + card2 + "H=true"
                evolution += " if\n"
                evolution += "\t\t\tcurrentPlayer=3 and clock>0 and EPlayer.Action=Play" + card + " and SPlayer.Action=Play" + card2 + ";\n"

            # Player E Plays, Player S Play N card

            for i2 in range(0, self.number_of_cards * 4):
                card2 = self.cards[i2]
                if card == card2:
                    continue

                for j in range(1, self.number_of_cards_in_hand + 1):
                    evolution += "\t\tcurrentPlayer=0 and clock=clock+1 and EPlayerCard=" + card + " and " + card + "H=true"
                    evolution += " and NPlayerCard=" + card2 + " and " + card2 + "H=true"
                    evolution += " and currentCardN" + str(j) + "=None"
                    evolution += " and suit=" + self.cards_colors[card]
                    evolution += " if\n"
                    evolution += "\t\t\tcurrentPlayer=3 and clock=0 and EPlayer.Action=Play" + card + " and SPlayer.Action=PlayN" + card2 + " and NPlayerCard=None"
                    evolution += " and currentCardN" + str(j) + "=" + card2
                    evolution += " and SPlayerCard=None"
                    evolution += ";\n"

                    evolution += "\t\tcurrentPlayer=1 and clock=clock+2 and EPlayerCard=" + card + " and " + card + "H=true"
                    evolution += " and NPlayerCard=" + card2 + " and " + card2 + "H=true"
                    evolution += " and currentCardN" + str(j) + "=None"
                    evolution += " and suit=" + self.cards_colors[card]
                    evolution += " if\n"
                    evolution += "\t\t\tcurrentPlayer=3 and clock=0 and EPlayer.Action=Play" + card + " and SPlayer.Action=PlayN" + card2 + " and NPlayerCard=None"
                    evolution += " and currentCardN" + str(j) + "=" + card2
                    evolution += " and !(SPlayerCard=None)"
                    evolution += ";\n"

                evolution += "\t\tcurrentPlayer=0 and clock=clock+1 and EPlayerCard=" + card + " and " + card + "H=true"
                evolution += " if\n"
                evolution += "\t\t\tcurrentPlayer=3 and clock>0 and EPlayer.Action=Play" + card + " and SPlayer.Action=PlayN" + card2 + " and !(NPlayerCard=None)"
                evolution += " and SPlayerCard=None"
                evolution += ";\n"

                evolution += "\t\tcurrentPlayer=1 and clock=clock+2 and EPlayerCard=" + card + " and " + card + "H=true"
                evolution += " if\n"
                evolution += "\t\t\tcurrentPlayer=3 and clock>0 and EPlayer.Action=Play" + card + " and SPlayer.Action=PlayN" + card2 + " and !(NPlayerCard=None)"
                evolution += " and !(SPlayerCard=None)"
                evolution += ";\n"

        evolution += "\tend Evolution\n"
        return evolution

    def __create_player(self, player_number):
        player = "Agent " + self.player_names[player_number] + "\n"
        if player_number != 0:
            player += self.__create_player_lobsvars()

        player += self.__create_player_vars(player_number)
        player += self.__create_player_actions(player_number)
        player += self.__create_player_protocol(player_number)
        player += self.__create_player_evolution(player_number)
        player += "end Agent\n\n"
        return player

    def __create_player_lobsvars(self):
        lobsvars = "\tLobsvars = {"
        for player in self.player_names:
            if player == self.player_names[0]:
                continue
            lobsvars += player + "Card, "

        for i in range(1, self.number_of_cards_in_hand + 1):
            lobsvars += "currentCardN" + str(i) + ", "

        lobsvars += "suit"
        lobsvars += "};\n"
        return lobsvars

    def __create_player_vars(self, player_number):
        vars = "\tVars:\n"
        for i in range(1, self.number_of_cards_in_hand + 1):
            vars += "\t\tcard" + str(i) + ": {"
            for j in range(0, 4 * self.number_of_cards):
                vars += self.cards[j] + ", "
            vars += "None};\n"

        if player_number != 0:
            for color in self.card_colors:
                vars += "\t\thas" + color + ": 0.." + str(self.number_of_cards_in_hand) + ";\n"

        vars += "\tend Vars\n"
        return vars

    def __create_player_actions(self, player_number):
        actions = "\tActions = {"
        for i in range(0, 4 * self.number_of_cards):
            actions += "Play" + self.cards[i] + ", "

        if player_number == 0:
            for i in range(0, 4 * self.number_of_cards):
                actions += "PlayN" + self.cards[i] + ", "

        actions += "Wait};\n"
        return actions

    def __create_player_protocol(self, player_number):
        protocol = "\tProtocol:\n"
        for i in range(1, self.number_of_cards_in_hand + 1):
            for j in range(0, 4 * self.number_of_cards):
                protocol += "\t\tcard" + str(i) + "=" + self.cards[j]
                if player_number != 0:
                    protocol += " and Environment.currentPlayer=" + str(
                        player_number) + " and Environment.clock<4 and (Environment.suit=None or Environment.suit=" + \
                                self.cards_colors[self.cards[
                                    j]] + " or ((hasSpade<=0 and Environment.suit=Spade) or (hasClub<=0 and Environment.suit=Club) or (hasDiamond<=0 and Environment.suit=Diamond) or (hasHeart<=0 and Environment.suit=Heart))):"
                else:
                    protocol += " and Environment.SPlayerCard=None:"
                protocol += " {Play" + self.cards[j]
                if player_number == 0:
                    protocol += ", Wait"

                protocol += "};\n"

        if player_number == 0:
            for i in range(1, self.number_of_cards_in_hand + 1):
                for j in range(0, 4 * self.number_of_cards):
                    protocol += "\t\tEnvironment.cardN" + str(i) + "=" + self.cards[j] + ":"
                    protocol += " {PlayN" + self.cards[j] + ", Wait};\n"

        protocol += "\t\tOther: {Wait};\n"
        protocol += "\tend Protocol\n"
        return protocol

    def __create_player_evolution(self, player_number):
        evolution = "\tEvolution:\n"
        for i in range(1, self.number_of_cards_in_hand + 1):
            for j in range(0, 4 * self.number_of_cards):
                evolution += "\t\tcard" + str(i) + "=None"
                if player_number != 0:
                    evolution += " and has" + self.cards_colors[self.cards[j]] + "=has" + \
                                 self.cards_colors[self.cards[j]] + "-1"
                evolution += " if card" + str(i)
                evolution += "=" + self.cards[j] + " and Action=Play" + self.cards[j]
                if player_number == 0:
                    evolution += " and Environment.SPlayerCard=None;\n"
                else:
                    evolution += " and Environment.currentPlayer=" + str(player_number) + ";\n"

        evolution += "\tend Evolution\n"
        return evolution

    def __create_evaluation(self):
        evaulation = "Evaluation\n"
        evaulation += "\tFirstTeamWin if Environment.firstTeamScore>Environment.secondTeamScore and Environment.firstTeamScore+Environment.secondTeamScore=" + str(
            self.number_of_cards_in_hand) + ";\n"
        evaulation += "\tSecondTeamWin if Environment.firstTeamScore<Environment.secondTeamScore and Environment.firstTeamScore+Environment.secondTeamScore=" + str(
            self.number_of_cards_in_hand) + ";\n"
        evaulation += "end Evaluation\n\n"
        return evaulation

    def __create_init_states(self):
        init_states = "InitStates\n"
        oponents_cards = []
        for k in range(self.number_of_cards_in_hand, self.number_of_cards_in_hand * 2):
            oponents_cards.append(self.card_ordering[k])

        for k in range(self.number_of_cards_in_hand * 3, self.number_of_cards_in_hand * 4):
            oponents_cards.append(self.card_ordering[k])

        oponents_cards.sort()
        number_of_beginning_states = 0

        for combination in itertools.combinations(oponents_cards, self.number_of_cards_in_hand):
            second_player_cards = combination
            fourth_player_cards = oponents_cards[:]
            for card in second_player_cards:
                fourth_player_cards.remove(card)

            new_card_ordering = self.card_ordering[:]
            i = 0
            for k in range(self.number_of_cards_in_hand, self.number_of_cards_in_hand * 2):
                new_card_ordering[k] = second_player_cards[i]
                i += 1

            i = 0
            for k in range(self.number_of_cards_in_hand * 3, self.number_of_cards_in_hand * 4):
                new_card_ordering[k] = fourth_player_cards[i]
                i += 1

            init_states += "\t(Environment.firstTeamScore=0 and Environment.secondTeamScore=0 and Environment.beginningPlayer=0 and Environment.currentPlayer=0 and Environment.clock=0 and Environment.SPlayerCard=None and Environment.WPlayerCard=None and Environment.NPlayerCard=None and Environment.EPlayerCard=None and Environment.suit=None"
            colors_count = {}
            i = 0
            for player in self.player_names:
                colors_count[player] = {}
                for color in self.card_colors:
                    colors_count[player][color] = 0
                for j in range(1, self.number_of_cards_in_hand + 1):
                    colors_count[player][self.cards_colors[self.cards[new_card_ordering[i]]]] += 1
                    i += 1
            i = 0
            for player in self.player_names:
                for color in self.card_colors:
                    if player != "NPlayer" and player != 'SPlayer':
                        init_states += " and " + player + ".has" + color + "=" + str(colors_count[player][color])

            for player in self.player_names:
                for j in range(1, self.number_of_cards_in_hand + 1):
                    if player == "NPlayer":
                        init_states += " and Environment.cardN" + str(j) + "=" + self.cards[new_card_ordering[i]]
                        init_states += " and Environment.currentCardN" + str(j) + "=" + self.cards[new_card_ordering[i]]
                    else:
                        init_states += " and " + player + ".card" + str(j) + "=" + self.cards[new_card_ordering[i]]
                    i += 1

            for j in range(0, self.number_of_cards * 4):
                init_states += " and Environment." + self.cards[j] + "H=false"

            init_states += ") or\n"
            number_of_beginning_states += 1

        print("Number of beginning states:", number_of_beginning_states)
        init_states = init_states.rstrip("\nro ")
        init_states += ";\nend InitStates\n\n"
        return init_states

    def __create_groups(self):
        groups = "Groups\n"
        groups += "\tg1={SPlayer};\n"
        groups += "end Groups\n\n"
        return groups

    def __create_formulae(self):
        formulae = "Formulae\n"
        formulae += "\t<g1>F FirstTeamWin;\n"
        formulae += "end Formulae\n\n"
        return formulae


def generate_random_array(length):
    array = []
    used = []
    for i in range(0, length):
        used.append(False)

    for i in range(0, length):
        number = random.randrange(length)
        while used[number]:
            number = random.randrange(length)

        array.append(number)
        used[number] = True

    return array


n = 2
k = 2
bridge_model_ispl_generator = BridgeModelIsplGenerator(n, n, generate_random_array(4 * n))
# bridge_model_ispl_generator = BridgeModelIsplGenerator(2, 2, [0, 7, 1, 2, 3, 4, 5, 6])
# bridge_model_ispl_generator = BridgeModelIsplGenerator(2, 2, [0, 1, 2, 3, 4, 5, 6, 7])
# bridge_model_ispl_generator = BridgeModelIsplGenerator(2, 2, [0, 7, 3, 4, 1, 2, 5, 6])
# bridge_model_ispl_generator = BridgeModelIsplGenerator(3, 3, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
# bridge_model_ispl_generator = BridgeModelIsplGenerator(2, 1, [4, 0, 5, 1])
f = open("blind_bridge_" + str(n) + "_" + str(k) + ".ispl", "w")
f.write(bridge_model_ispl_generator.create_ispl_model())
f.close()
