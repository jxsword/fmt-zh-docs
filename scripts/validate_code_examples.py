#!/usr/bin/env python3
"""Validate C++ code examples in translated documentation."""

import logging
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.resolve()
ZH_DIR = REPO_ROOT / "zh"


@dataclass
class ValidationResult:
    success: bool
    compiler: str
    error: str = ""


def extract_cpp_blocks(content: str) -> List[Tuple[int, str]]:
    blocks = []
    lines = content.split('\n')
    in_block = False
    block_start = 0
    block_lines = []
    for i, line in enumerate(lines):
        if line.strip().startswith('```cpp') or line.strip().startswith('```c++'):
            if in_block:
                logger.warning("Nested code block at line %d", i+1)
            in_block = True
            block_start = i + 1
            block_lines = []
        elif line.strip() == '```' and in_block:
            in_block = False
            if block_lines:
                code = '\n'.join(block_lines)
                blocks.append((block_start, code))
        elif in_block:
            block_lines.append(line)
    return blocks


def wrap_code_for_compilation(code: str) -> str:
    if re.search(r'int\s+main\s*\(', code):
        return code
    has_fmt = 'fmt::' in code
    has_std = 'std::' in code
    wrapper = []
    wrapper.append('#include <fmt/format.h>')
    if has_fmt or has_std:
        wrapper.append('#include <fmt/ranges.h>')
        wrapper.append('#include <fmt/chrono.h>')
        wrapper.append('#include <vector>')
        wrapper.append('#include <chrono>')
    wrapper.append('')
    wrapper.append('int main() {')
    wrapper.append('    ' + code.replace('\n', '\n    '))
    wrapper.append('    return 0;')
    wrapper.append('}')
    return '\n'.join(wrapper)


def compile_gpp(code: str) -> ValidationResult:
    with tempfile.NamedTemporaryFile(suffix='.cpp', mode='w', delete=False) as f:
        f.write(code)
        temp_path = f.name
    try:
        result = subprocess.run(
            ['g++', '-std=c++20', '-O2', temp_path, '-lfmt'],
            capture_output=True, text=True, timeout=30, shell=False
        )
        if result.returncode == 0:
            return ValidationResult(True, 'g++')
        return ValidationResult(False, 'g++', result.stderr)
    except subprocess.TimeoutExpired:
        return ValidationResult(False, 'g++', "Compilation timeout")
    except FileNotFoundError:
        return ValidationResult(False, 'g++', "Compiler not found: g++")
    except Exception as e:
        return ValidationResult(False, 'g++', str(e))
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass


def compile_clang(code: str) -> ValidationResult:
    with tempfile.NamedTemporaryFile(suffix='.cpp', mode='w', delete=False) as f:
        f.write(code)
        temp_path = f.name
    try:
        result = subprocess.run(
            ['clang++', '-std=c++20', '-O2', temp_path, '-lfmt'],
            capture_output=True, text=True, timeout=30, shell=False
        )
        if result.returncode == 0:
            return ValidationResult(True, 'clang++')
        return ValidationResult(False, 'clang++', result.stderr)
    except subprocess.TimeoutExpired:
        return ValidationResult(False, 'clang++', "Compilation timeout")
    except FileNotFoundError:
        return ValidationResult(False, 'clang++', "Compiler not found: clang++")
    except Exception as e:
        return ValidationResult(False, 'clang++', str(e))
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass


def compile_msvc(code: str) -> ValidationResult:
    with tempfile.NamedTemporaryFile(suffix='.cpp', mode='w', delete=False) as f:
        f.write(code)
        temp_path = f.name
    try:
        result = subprocess.run(
            ['cl', '/std:c++20', '/O2', temp_path, 'fmt.lib'],
            capture_output=True, text=True, timeout=30, shell=False
        )
        if result.returncode == 0:
            return ValidationResult(True, 'cl')
        return ValidationResult(False, 'cl', result.stderr)
    except subprocess.TimeoutExpired:
        return ValidationResult(False, 'cl', "Compilation timeout")
    except FileNotFoundError:
        return ValidationResult(False, 'cl', "Compiler not found: cl")
    except Exception as e:
        return ValidationResult(False, 'cl', str(e))
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass


@dataclass
class ValidationResult:
    success: bool
    compiler: str
    error: str = ""


def extract_cpp_blocks(content: str) -> List[Tuple[int, str]]:
    blocks = []
    lines = content.split('\n')
    in_block = False
    block_start = 0
    block_lines = []
    for i, line in enumerate(lines):
        if line.strip().startswith('```cpp') or line.strip().startswith('```c++'):
            if in_block:
                logger.warning("Nested code block at line %d", i+1)
            in_block = True
            block_start = i + 1
            block_lines = []
        elif line.strip() == '```' and in_block:
            in_block = False
            if block_lines:
                code = '\n'.join(block_lines)
                blocks.append((block_start, code))
        elif in_block:
            block_lines.append(line)
    return blocks


def wrap_code_for_compilation(code: str) -> str:
    if re.search(r'int\s+main\s*\(', code):
        return code
    has_fmt = 'fmt::' in code
    has_std = 'std::' in code
    wrapper = []
    wrapper.append('#include <fmt/format.h>')
    if has_fmt or has_std:
        wrapper.append('#include <fmt/ranges.h>')
        wrapper.append('#include <fmt/chrono.h>')
        wrapper.append('#include <vector>')
        wrapper.append('#include <chrono>')
    wrapper.append('')
    wrapper.append('int main() {')
    wrapper.append('    ' + code.replace('\n', '\n    '))
    wrapper.append('    return 0;')
    wrapper.append('}')
    return '\n'.join(wrapper)


def validate_file(filepath: Path) -> List[str]:
    content = filepath.read_text(encoding='utf-8')
    blocks = extract_cpp_blocks(content)
    errors = []
    for line_num, code in blocks:
        wrapped = wrap_code_for_compilation(code)
        compiled = False
        for compiler_func in (compile_gpp, compile_clang):
            result = compiler_func(wrapped)
            if result.success:
                compiled = True
                break
        if not compiled:
            errors.append(f"{filepath}:{line_num}: Failed to compile with all compilers")
            logger.error("Failed to compile code at %s:%d", filepath, line_num)
            logger.debug("Code:\n%s", code)
    return errors


def main():
    if len(sys.argv) > 1:
        files = [Path(f) for f in sys.argv[1:]]
    else:
        files = list(ZH_DIR.glob("*.md"))
    all_errors = []
    for filepath in files:
        logger.info("Validating %s", filepath)
        errors = validate_file(filepath)
        all_errors.extend(errors)
    if all_errors:
        logger.error("Validation failed with %d errors:", len(all_errors))
        for err in all_errors:
            logger.error("  %s", err)
        sys.exit(1)
    else:
        logger.info("All code examples validated successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()