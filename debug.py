from lark import Lark

if __name__ == "__main__":
    text = """Fees for completing surveys for YouGov, 50 Featherstone Street, London EC1Y 8RT:"""
    with open("grammars/payment.lark", "r") as grammar:
        parser = Lark(grammar, debug=True)
        parser.parse(text)
