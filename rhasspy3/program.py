import asyncio
import logging
import os
import shlex
import string
from asyncio import subprocess
from typing import Optional, Union

from .config import PipelineProgramConfig, ProgramConfig
from .core import Rhasspy
from .util import merge_dict

_LOGGER = logging.getLogger(__name__)


class MissingProgramConfigError(Exception):
    pass


# pylint: disable=no-member
async def create_process(
    rhasspy: Rhasspy, domain: str, name: Union[str, PipelineProgramConfig]
) -> subprocess.Process:
    pipeline_config: Optional[PipelineProgramConfig] = None
    if isinstance(name, PipelineProgramConfig):
        pipeline_config = name
        name = pipeline_config.name

    program_config: Optional[ProgramConfig] = rhasspy.config.programs.get(
        domain, {}
    ).get(name)
    assert program_config is not None, f"No config for program {domain}/{name}"
    assert isinstance(program_config, ProgramConfig)

    command_str = program_config.command.strip()
    mapping = program_config.template_args or {}

    if pipeline_config is not None:
        if pipeline_config.template_args:
            merge_dict(mapping, pipeline_config.template_args)

    if mapping:
        command_template = string.Template(command_str)
        command_str = command_template.safe_substitute(mapping)

    working_dir = rhasspy.config_dir / "programs" / domain / name
    env = dict(os.environ)

    # Add rhasspy3/bin to $PATH
    env["PATH"] = f'{rhasspy.base_dir}/bin:${env["PATH"]}'

    # Ensure stdout is flushed for Python programs
    env["PYTHONUNBUFFERED"] = "1"

    cwd = working_dir if working_dir.is_dir() else None

    if program_config.shell:
        if program_config.adapter:
            program, *args = shlex.split(program_config.adapter)
            args.append("--shell")
            args.append(command_str)

            proc = await asyncio.create_subprocess_exec(
                program,
                *args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                cwd=cwd,
                env=env,
            )
        else:
            proc = await asyncio.create_subprocess_shell(
                command_str,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                cwd=cwd,
                env=env,
            )
    else:
        if program_config.adapter:
            program, *args = shlex.split(program_config.adapter)
            args.append(command_str)
        else:
            program, *args = shlex.split(command_str)

        proc = await asyncio.create_subprocess_exec(
            program,
            *args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=cwd,
            env=env,
        )

    return proc
