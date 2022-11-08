import psycopg2


class Database():
    def __init__(self, host, password, user, db_name):
        self.connection = psycopg2.connect(
            host=host,
            password=password,
            user=user,
            database=db_name,
        )
        self.connection.autocommit = False
        self.cursor = self.connection.cursor()

    def user_exists(self, user_id):
        try:
            with self.connection:
                self.cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                if len(self.cursor.fetchall()) != 0:
                    return True
                else:
                    return False
        except Exception as ex:
            self.connection.rollback()
            return f'{ex}'

    def add_user(self, user_id, nickname):
        try:
            with self.connection:
                self.cursor.execute("INSERT INTO users (user_id, nickname) VALUES (%s, %s)", (user_id, nickname,))
                self.cursor.execute("INSERT INTO phones (user_id, phone_number) VALUES (%s, %s)", (user_id, "11",))
                self.cursor.execute("INSERT INTO balances (user_id) VALUES (%s)", (user_id,))
                self.connection.commit()
        except Exception as ex:
            self.connection.rollback()
            return f"Transaction Failed {ex}"

    def set_phone(self, user_id, phone):
        try:
            with self.connection:
                self.cursor.execute("UPDATE phones SET phone_number = %s WHERE user_id = %s", (phone, user_id,))
                self.connection.commit()
        except Exception as ex:
            self.connection.rollback()
            return f'{ex}'

    def get_phone(self, user_id):
        try:
            with self.connection:
                self.cursor.execute("SELECT phone_number FROM phones WHERE user_id = %s", (user_id,))
                result = self.cursor.fetchone()[0]
                return result
        except Exception:
            return f'ERROR'

    def phone_exists(self, phone):
        try:
            with self.connection:
                self.cursor.execute("SELECT * FROM phones WHERE phone_number = %s", (phone,))
                if len(self.cursor.fetchall()) != 0:
                    return True
                else:
                    return False
        except Exception:
            self.connection.rollback()

    def get_user_by_phone(self, phone):
        try:
            with self.connection:
                self.cursor.execute("SELECT users.nickname FROM users INNER JOIN phones ON phones.phone_number=%s AND users.user_id=phones.user_id;", (phone,))
                return self.cursor.fetchone()[0]
        except Exception:
            return f'ERROR'

    def get_action(self, user_id):
        try:
            with self.connection:
                self.cursor.execute("SELECT action FROM users WHERE user_id = %s", (user_id,))
                return self.cursor.fetchone()[0]
        except Exception:
            return f"ERROR"

    def set_action(self, user_id, action):
        try:
            with self.connection:
                self.cursor.execute("UPDATE users SET action = %s WHERE user_id = %s", (action, user_id,))
                self.connection.commit()
        except Exception:
            self.connection.rollback()

    def set_nickname(self, user_id, nickname):
        try:
            with self.connection:
                self.cursor.execute("UPDATE users SET nickname = %s WHERE user_id = %s", (nickname, user_id,))
                self.connection.commit()
        except Exception:
            self.connection.rollback()

    def get_nickname(self, user_id):
        try:
            with self.connection:
                self.cursor.execute("SELECT nickname FROM users WHERE user_id = %s", (user_id,))
                result = self.cursor.fetchone()[0]
                return result
        except Exception:
            return f'ERROR'

    def get_balance(self, user_id):
        try:
            with self.connection:
                self.cursor.execute("SELECT balance FROM balances WHERE user_id = %s", (user_id,))
                return self.cursor.fetchone()[0]
        except Exception:
            return f'ERROR'

    def set_balance(self, user_id, balance):
        try:
            current_balance = self.get_balance(user_id)
            with self.connection:
                self.connection.autocommit = False
                self.cursor.execute("UPDATE balances SET balance = %s WHERE user_id = %s", (float(current_balance) + float(balance), user_id,))
        except Exception as ex:
            self.connection.rollback()
            return f'{ex}'

    def transfer(self, user_id, phone, balance):
        try:
            # self.set_balance(user_id, -balance)
            current_balance = self.get_balance(user_id)
            with self.connection:
                self.cursor.execute("UPDATE balances SET balance = %s WHERE user_id = %s", (float(current_balance) - float(balance), user_id,))
                self.cursor.execute("SELECT user_id FROM phones WHERE phone_number = %s", (phone,))
                dest = self.cursor.fetchone()[0]
                self.cursor.execute("SELECT balance FROM balances WHERE user_id = %s", (dest,))
                current_dest_balance = self.cursor.fetchone()[0]
                self.cursor.execute("UPDATE balances SET balance = %s WHERE user_id = %s", (float(current_dest_balance) + float(balance), dest,))
            # self.set_balance(dest, balance)
        except Exception as ex:
            self.connection.rollback()
            return f'{ex}'

    def get_user_id_by_phone(self, phone):
        try:
            with self.connection:
                self.cursor.execute("SELECT user_id FROM phones WHERE phone_number = %s", (phone,))
                result = self.cursor.fetchone()[0]
                return result
        except Exception:
            return f'ERROR'

    def notification(self, user_id, balance):
        try:
            with self.connection:
                self.cursor.execute("SELECT nickname FROM users WHERE user_id = %s", (user_id,))
                name = self.cursor.fetchone()[0]
                return f'Вам поступил перевод: {balance}\nОт {name}'
        except Exception:
            return f'ERROR'

    def set_transaction_info(self, send_name, dest_name, transfer_amount, time):
        try:
            with self.connection:
                self.cursor.execute("INSERT INTO transactions(send_name, dest_name, transfer_amount, transaction_time) VALUES (%s, %s, %s, %s)", (send_name, dest_name, transfer_amount, time,))
        except Exception as ex:
            self.connection.rollback()
            return f'{ex}'

    def get_transaction_info(self, user_id):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT nickname FROM users WHERE user_id = %s", (user_id,))
                name = cursor.fetchone()[0]
                cursor.execute("SELECT dest_name, transfer_amount, transaction_time FROM transactions WHERE send_name=%s", (name,))
                for row in cursor:
                    yield row
        except Exception as ex:
            return f'{ex}'

    def show_info(self, user_id):
        with self.connection:
            self.cursor.execute("SELECT phones.phone_number, users.user_id, users.nickname,balances.balance FROM phones INNER JOIN users ON users.user_id=%s INNER JOIN balances ON balances.user_id=%s WHERE phones.user_id=%s", (user_id, user_id, user_id,))
            result = self.cursor.fetchone()
            phone = result[0]
            us_id = result[1]
            nickname = result[2]
            balance = result[3]
            return f'id: {us_id}\nНикнeйм: {nickname}\nБaлaнc: {round(balance,2)}\nНомер телефона: {phone}'
