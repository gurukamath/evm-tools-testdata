import argparse
import json
import os
import sys

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
)

parser.add_argument("--testdata", dest="testdata", type=int, required=True)
parser.add_argument("--fork", dest="fork", type=str, required=True)

if __name__ == "__main__":
    options = parser.parse_args()

    with open("commands.json", "r") as f:
        cmds = json.load(f)

    key = f"fixtures/expected/{options.testdata}/{options.fork}.json"

    if key in cmds:
        value_list = cmds[key]
        cmd = "evm"
        for value in value_list["args"]:
            cmd += " "
            if "__BASEDIR__" in value:
                cmd += value.replace("__BASEDIR__", "../t8n")
            else:
                cmd += value
    else:
        sys.exit(f"Command for {key} not found.")

    print(cmd)
