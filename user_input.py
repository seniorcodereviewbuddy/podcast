import typing

PromptYesOrNo_Alias = typing.Callable[[str], bool]


def PromptYesOrNo(user_prompt: str) -> bool:
    while True:
        print(user_prompt + "\n(Y/N)? ", end="")
        result = input()
        if result not in ("y", "Y", "n", "N"):
            print("Unclear input, expecting y/Y/n/N. Please try again.")
            continue
        return result in ("y", "Y")
