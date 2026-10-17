import unittest
from unittest.mock import patch

import app as web


class WebGameTests(unittest.TestCase):
    def setUp(self):
        web.app.config.update(TESTING=True, SECRET_KEY="test-only-key")
        self.client = web.app.test_client()

    def csrf_token(self, client=None):
        client = client or self.client
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        with client.session_transaction() as browser_session:
            return browser_session["csrf_token"]

    def post_action(self, action, client=None):
        client = client or self.client
        return client.post(
            "/action",
            data={"action": action, "csrf_token": self.csrf_token(client)},
            follow_redirects=True,
        )

    def test_home_renders_player_and_actions(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Emberfall", response.data)
        self.assertIn(b"Find battle", response.data)
        self.assertIn(b"Health", response.data)

    def test_visitors_receive_independent_browser_saves(self):
        second_visitor = web.app.test_client()
        self.post_action("find_battle", self.client)
        self.csrf_token(second_visitor)

        with self.client.session_transaction() as first_session:
            first_state = first_session["game_state"]
        with second_visitor.session_transaction() as second_session:
            second_state = second_session["game_state"]

        self.assertIsNotNone(first_state["battle"])
        self.assertIsNone(second_state["battle"])

    def test_battle_action_awards_rewards_and_clears_enemy(self):
        with self.client.session_transaction() as browser_session:
            browser_session["game_state"] = web.game.new_state()
            browser_session["game_state"]["battle"] = {
                "enemy": {
                    "name": "Goblin",
                    "hp": 1,
                    "max_hp": 30,
                    "attack": 1,
                    "xp": 10,
                    "gold": 5,
                }
            }
        with patch.object(web.game.random, "randint", return_value=12):
            response = self.post_action("attack")

        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as browser_session:
            state = browser_session["game_state"]
        self.assertIsNone(state["battle"])
        self.assertEqual(state["player"]["gold"], 5)
        self.assertIn(b"Victory", response.data)

    def test_csrf_token_is_required(self):
        response = self.client.post("/action", data={"action": "rest"})
        self.assertEqual(response.status_code, 400)

    def test_web_actions_do_not_write_shared_json_save(self):
        with patch.object(web.game, "save_game") as save_game:
            self.post_action("rest")
            self.post_action("find_battle")
            self.post_action("use_potion")
            self.post_action("buy_potion")
        save_game.assert_not_called()

    def test_rest_is_blocked_during_battle(self):
        with self.client.session_transaction() as browser_session:
            state = web.game.new_state()
            state["battle"] = {
                "enemy": {
                    "name": "Goblin",
                    "hp": 10,
                    "max_hp": 30,
                    "attack": 6,
                    "xp": 10,
                    "gold": 5,
                }
            }
            browser_session["game_state"] = state

        response = self.post_action("rest")
        with self.client.session_transaction() as browser_session:
            state = browser_session["game_state"]
        self.assertEqual(state["player"]["hp"], 100)
        self.assertIn(b"cannot rest", response.data)


if __name__ == "__main__":
    unittest.main()
