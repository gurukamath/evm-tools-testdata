import json
import os
import shutil
import subprocess
from copy import deepcopy
from typing import Any, Dict, List, Optional

geth_evm_path = "../go-ethereum/build/bin/evm"

base_dir = "."

forks = [
    "Frontier",
    "Homestead",
    "EIP150",
    "EIP158",
    "Byzantium",
    "ConstantinopleFix",
    "Istanbul",
    "MuirGlacier",
    "Berlin",
    "London",
    "ArrowGlacier",
    "GrayGlacier",
    "Merge",
    "Shanghai",
]

extra_params_dict = {5: ["--state.reward", "128"]}


def set_base_dir(args: Any, subprocess_args: Any) -> None:
    """Set the base directory for the testdata"""
    for arg in args:
        if "__BASEDIR__" in arg:
            subprocess_args.append(arg.replace("__BASEDIR__", base_dir))
        else:
            subprocess_args.append(arg)


def get_args(testdata: int, fork: str, extra_params: Optional[List[str]] = None) -> Any:
    if extra_params is None:
        extra_params = []

    args = [
        "t8n",
        "--input.alloc",
        f"__BASEDIR__/t8n/fixtures/testdata/{testdata}/alloc.json",
        "--input.env",
        f"__BASEDIR__/t8n/fixtures/testdata/{testdata}/env.json",
        "--input.txs",
        f"__BASEDIR__/t8n/fixtures/testdata/{testdata}/txs.json",
    ]

    args += ["--state.fork", fork] + extra_params

    return args


def get_testdata() -> Any:
    test_dirs = [
        f.path
        for f in os.scandir(
            os.path.join(base_dir, "t8n", "fixtures", "testdata")
        )
        if f.is_dir()
    ]
    testdata = []
    for test_dir in test_dirs:
        try:
            testdata.append(int(test_dir.split("/")[-1]))
        except ValueError:
            continue

    return testdata


def main() -> None:
    expected_path = os.path.join("t8n", "fixtures", "expected")
    commands_path = "t8n_commands.json"

    if os.path.exists(commands_path):
        os.remove(commands_path)

    if os.path.exists(expected_path):
        shutil.rmtree(expected_path)

    os.mkdir(expected_path)

    auto_commands: Dict[Any, Any] = {}
    for testdata in get_testdata():
        extra_params: Optional[List[str]] = None
        for fork in forks:
            parameters: Dict[Any, Any] = {}

            output_dir = os.path.join(expected_path, str(testdata))
            output_file = os.path.join(output_dir, f"{fork}.json")

            if testdata in extra_params_dict:
                extra_params = extra_params_dict[testdata]

            args = get_args(testdata, fork, extra_params)
            auto_commands[output_file] = {}
            auto_commands[output_file]["args"] = args

    with open("t8n/custom_tests.json", "r") as f:
        custom_commands = json.load(f)

    all_commands = {**auto_commands, **custom_commands}
    cmds = {}

    for output_file, arguments in all_commands.items():
        parameters = {}
        parameters = arguments

        subprocess_args = [geth_evm_path]
        set_base_dir(arguments["args"], subprocess_args)

        output_file_alloc = output_file.replace(".json", "_alloc.json")
        output_file_result = output_file.replace(".json", "_result.json")
        output_file_body = output_file.replace(".json", "_txs.rlp")
        output_dir = os.path.dirname(output_file)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        subprocess_args += [
            "--output.alloc",
            output_file_alloc,
            "--output.result",
            output_file_result,
            "--output.body",
            output_file_body,
        ]

        # Run subprocess hide the output and capture only the error
        subproc_run = subprocess.run(
            subprocess_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if subproc_run.returncode:
            print(
                output_file.split("/")[-2:],
                "\n",
                subproc_run.stderr.decode("utf-8").replace("\n", ""),
            )
            # parameters["success"] = False
            # cmds[output_file] = deepcopy(parameters)
            continue

        parameters["success"] = True
        cmds[output_file] = deepcopy(parameters)

        with open(output_file_alloc, "r") as f:
            alloc = json.load(f)

        with open(output_file_result, "r") as f:
            result = json.load(f)

        with open(output_file_body, "r") as f:
            body = f.read()

        output = {}
        output["alloc"] = alloc
        output["result"] = result
        output["txs_rlp"] = body[1:-1]

        with open(output_file, "w") as f:
            json.dump(output, f, indent=4)

        os.remove(output_file_alloc)
        os.remove(output_file_result)
        os.remove(output_file_body)

    with open(commands_path, "w") as f:
        json.dump(cmds, f, indent=4)


if __name__ == "__main__":
    main()
