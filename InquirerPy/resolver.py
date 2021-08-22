"""This module contains the classic entrypoint for creating prompts.

A `PyInquirer <https://github.com/CITGuru/PyInquirer>`_ compatible entrypoint :func:`.prompt`.
"""
from typing import Any, Dict, List, Union

from InquirerPy.exceptions import InvalidArgument, RequiredKeyNotFound
from InquirerPy.prompts.checkbox import CheckboxPrompt
from InquirerPy.prompts.confirm import ConfirmPrompt
from InquirerPy.prompts.expand import ExpandPrompt
from InquirerPy.prompts.filepath import FilePathPrompt
from InquirerPy.prompts.fuzzy import FuzzyPrompt
from InquirerPy.prompts.input import InputPrompt
from InquirerPy.prompts.list import ListPrompt
from InquirerPy.prompts.rawlist import RawlistPrompt
from InquirerPy.prompts.secret import SecretPrompt
from InquirerPy.utils import SessionResult, get_style

__all__ = ["prompt"]

question_mapping = {
    "confirm": ConfirmPrompt,
    "filepath": FilePathPrompt,
    "password": SecretPrompt,
    "input": InputPrompt,
    "list": ListPrompt,
    "checkbox": CheckboxPrompt,
    "rawlist": RawlistPrompt,
    "expand": ExpandPrompt,
    "fuzzy": FuzzyPrompt,
}

list_prompts = {"list", "checkbox", "rawlist", "expand", "fuzzy"}


def prompt(
    questions: Union[List[Dict[str, Any]], Dict[str, Any]],
    style: Dict[str, str] = None,
    vi_mode: bool = False,
    raise_keyboard_interrupt: bool = True,
    keybindings: Dict[str, List[Dict[str, Any]]] = None,
    style_override: bool = True,
) -> SessionResult:
    """Classic syntax entrypoint to create a prompt session.

    Resolve user provided list of questions, display prompts and get the results.

    Args:
        questions: A list of :ref:`pages/prompt:question` to ask. Refer to documentation for more info.
        style: A dictionary of :ref:`pages/style:Style`. Refer to documentation for more info.
        vi_mode: Use vim keybindings for the prompt instead of the default emacs keybindings.
        raise_keyboard_interrupt: Raise the kbi exception when user hit `ctrl-c`. If false, the result
            will be `None` and the question is skiped.
        keybindings: List of custom :ref:`pages/kb:Keybindings` to apply. Refer to documentation for more info.
        style_override: Override all default styles.
            When providing any customization, all default styles are cleared when this is True.

    Returns:
        A dictionary containing all of the question answers. The key is the name of the question and the value is the
        user answer. If the `name` key is not present as part of the question, then the question index will be used
        as the key.

    Raises:
        RequiredKeyNotFound: When the question is missing required keys.
        InvalidArgument: When the provided `questions` argument is not a type of :class:`list` nor :class:`dictionary`.

    Examples:
        >>> from InquirerPy import prompt
        >>> from InquirerPy.validator import NumberValidator
        >>> questions = [
        ...     {
        ...         "type": "input",
        ...         "message": "Enter your age:",
        ...         "validate": NumberValidator(),
        ...         "invalid_message": "Input should be number.",
        ...         "default": "18",
        ...         "name": "age",
        ...         "filter": lambda result: int(result),
        ...         "transformer": lambda result: "Adult" if int(result) >= 18 else "Youth",
        ...     },
        ...     {
        ...         "type": "rawlist",
        ...         "message": "What drinks would you like to buy:",
        ...         "default": 2,
        ...         "choices": lambda result: ["Soda", "Cidr", "Water", "Milk"]
        ...         if result["age"] < 18
        ...         else ["Wine", "Beer"],
        ...         "name": "drink",
        ...     },
        ...     {
        ...         "type": "list",
        ...         "message": "Would you like a bag:",
        ...         "choices": ["Yes", "No"],
        ...         "when": lambda result: result["drink"] in {"Wine", "Beer"},
        ...     },
        ...     {"type": "confirm", "message": "Confirm?", "default": True},
        ... ]
        >>> result = prompt(questions=questions)
    """
    result: SessionResult = {}
    if not keybindings:
        keybindings = {}

    if isinstance(questions, dict):
        questions = [questions]

    if not isinstance(questions, list):
        raise InvalidArgument("argument questions should be type of list or dictionary")

    question_style = get_style(style, style_override)

    for index, original_question in enumerate(questions):
        try:
            question = original_question.copy()
            question_type = question.pop("type")
            question_name = question.pop("name", index)
            message = question.pop("message")
            question_when = question.pop("when", None)
            if question_when and not question_when(result):
                result[question_name] = None
                continue
            args = {
                "message": message,
                "style": question_style,
                "vi_mode": vi_mode,
                "session_result": result,
            }
            if question_type in list_prompts:
                args["keybindings"] = {**keybindings, **question.pop("keybindings", {})}
            result[question_name] = question_mapping[question_type](
                **args, **question
            ).execute(raise_keyboard_interrupt=raise_keyboard_interrupt)
        except KeyError:
            raise RequiredKeyNotFound

    return result
