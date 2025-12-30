import typing
import unittest
import unittest.mock

import user_input

# Test constants
_TEST_PROMPT = "Continue?"
_PROMPT_SUFFIX = "\n(Y/N)? "
_ERROR_MESSAGE = "Unclear input, expecting y/Y/n/N. Please try again."


class TestPromptYesOrNo(unittest.TestCase):
    @unittest.mock.patch("builtins.input", return_value="y")
    @unittest.mock.patch("builtins.print")
    def test_prompt_yes_or_no_lowercase_y(
        self, mock_print: typing.Any, mock_input: typing.Any
    ) -> None:
        result = user_input.prompt_yes_or_no(_TEST_PROMPT)
        self.assertTrue(result)
        mock_print.assert_called_once_with(_TEST_PROMPT + _PROMPT_SUFFIX, end="")
        mock_input.assert_called_once()

    @unittest.mock.patch("builtins.input", return_value="Y")
    @unittest.mock.patch("builtins.print")
    def test_prompt_yes_or_no_uppercase_y(
        self, mock_print: typing.Any, mock_input: typing.Any
    ) -> None:
        result = user_input.prompt_yes_or_no(_TEST_PROMPT)
        self.assertTrue(result)
        mock_print.assert_called_once_with(_TEST_PROMPT + _PROMPT_SUFFIX, end="")
        mock_input.assert_called_once()

    @unittest.mock.patch("builtins.input", return_value="n")
    @unittest.mock.patch("builtins.print")
    def test_prompt_yes_or_no_lowercase_n(
        self, mock_print: typing.Any, mock_input: typing.Any
    ) -> None:
        result = user_input.prompt_yes_or_no(_TEST_PROMPT)
        self.assertFalse(result)
        mock_print.assert_called_once_with(_TEST_PROMPT + _PROMPT_SUFFIX, end="")
        mock_input.assert_called_once()

    @unittest.mock.patch("builtins.input", return_value="N")
    @unittest.mock.patch("builtins.print")
    def test_prompt_yes_or_no_uppercase_n(
        self, mock_print: typing.Any, mock_input: typing.Any
    ) -> None:
        result = user_input.prompt_yes_or_no(_TEST_PROMPT)
        self.assertFalse(result)
        mock_print.assert_called_once_with(_TEST_PROMPT + _PROMPT_SUFFIX, end="")
        mock_input.assert_called_once()

    @unittest.mock.patch("builtins.input", side_effect=["yes", "y"])
    @unittest.mock.patch("builtins.print")
    def test_prompt_yes_or_no_invalid_then_valid(
        self, mock_print: typing.Any, mock_input: typing.Any
    ) -> None:
        result = user_input.prompt_yes_or_no(_TEST_PROMPT)
        self.assertTrue(result)
        self.assertEqual(mock_print.call_count, 3)
        # First call: initial prompt
        self.assertEqual(
            mock_print.call_args_list[0][0][0], _TEST_PROMPT + _PROMPT_SUFFIX
        )
        # Second call: error message
        self.assertEqual(
            mock_print.call_args_list[1][0][0],
            _ERROR_MESSAGE,
        )
        # Third call: re-prompt
        self.assertEqual(
            mock_print.call_args_list[2][0][0], _TEST_PROMPT + _PROMPT_SUFFIX
        )
        self.assertEqual(mock_input.call_count, 2)

    @unittest.mock.patch("builtins.input", side_effect=["maybe", "sure", "Y"])
    @unittest.mock.patch("builtins.print")
    def test_prompt_yes_or_no_multiple_invalid_inputs(
        self, mock_print: typing.Any, mock_input: typing.Any
    ) -> None:
        result = user_input.prompt_yes_or_no(_TEST_PROMPT)
        self.assertTrue(result)
        self.assertEqual(mock_print.call_count, 5)
        # Verify error messages were printed
        self.assertEqual(
            mock_print.call_args_list[1][0][0],
            _ERROR_MESSAGE,
        )
        self.assertEqual(
            mock_print.call_args_list[3][0][0],
            _ERROR_MESSAGE,
        )
        self.assertEqual(mock_input.call_count, 3)

    @unittest.mock.patch("builtins.input", side_effect=["", "y"])
    @unittest.mock.patch("builtins.print")
    def test_prompt_yes_or_no_empty_input(
        self, mock_print: typing.Any, mock_input: typing.Any
    ) -> None:
        result = user_input.prompt_yes_or_no(_TEST_PROMPT)
        self.assertTrue(result)
        self.assertEqual(mock_print.call_count, 3)
        self.assertEqual(
            mock_print.call_args_list[1][0][0],
            _ERROR_MESSAGE,
        )
        self.assertEqual(mock_input.call_count, 2)

    @unittest.mock.patch("builtins.input", side_effect=["yes", "no", "1", "0", "Y"])
    @unittest.mock.patch("builtins.print")
    def test_prompt_yes_or_no_various_invalid_inputs(
        self, mock_print: typing.Any, mock_input: typing.Any
    ) -> None:
        result = user_input.prompt_yes_or_no(_TEST_PROMPT)
        self.assertTrue(result)
        # Should have prompted 5 times and shown 4 error messages
        self.assertEqual(mock_print.call_count, 9)
        self.assertEqual(mock_input.call_count, 5)

    @unittest.mock.patch("builtins.input", return_value="y")
    @unittest.mock.patch("builtins.print")
    def test_prompt_yes_or_no_with_custom_message(
        self, mock_print: typing.Any, mock_input: typing.Any
    ) -> None:
        custom_prompt = "Do you want to delete all files?"
        result = user_input.prompt_yes_or_no(custom_prompt)
        self.assertTrue(result)
        mock_print.assert_called_once_with(f"{custom_prompt}\n(Y/N)? ", end="")

    @unittest.mock.patch("builtins.input", return_value="y")
    @unittest.mock.patch("builtins.print")
    def test_prompt_yes_or_no_with_unicode_message(
        self, mock_print: typing.Any, mock_input: typing.Any
    ) -> None:
        unicode_prompt = "Продолжить? 继续？ 🎧"
        result = user_input.prompt_yes_or_no(unicode_prompt)
        self.assertTrue(result)
        mock_print.assert_called_once_with(f"{unicode_prompt}\n(Y/N)? ", end="")


if __name__ == "__main__":
    unittest.main()
