#!/usr/bin/env python3
"""
MOSS v9.3.0 - Release Checklist Script
发布前检查清单

Usage: python scripts/release_checklist.py
"""

import ast
import os
import subprocess
import sys
from pathlib import Path


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_section(title: str):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")


def check_ok(message: str):
    print(f"{Colors.GREEN}✓{Colors.END} {message}")


def check_fail(message: str):
    print(f"{Colors.RED}✗{Colors.END} {message}")
    return False


def check_warn(message: str):
    print(f"{Colors.YELLOW}⚠{Colors.END} {message}")


class ReleaseChecker:
    def __init__(self, root_path: str = "."):
        self.root = Path(root_path).resolve()
        self.errors = []
        self.warnings = []

    def run_all_checks(self) -> bool:
        """运行所有检查"""
        print_section("MOSS v9.3.0 Release Checklist")

        checks = [
            self.check_version_consistency,
            self.check_file_structure,
            self.check_imports,
            self.check_cli_entry_point,
            self.check_documentation,
            self.check_tests,
            self.check_ci_cd_files,
        ]

        all_passed = True
        for check in checks:
            try:
                if not check():
                    all_passed = False
            except Exception as e:
                check_fail(f"{check.__name__} failed: {e}")
                all_passed = False

        print_section("Summary")
        if all_passed:
            check_ok("All checks passed! Ready for release.")
        else:
            check_fail("Some checks failed. Please fix before release.")
            if self.errors:
                print(f"\n{Colors.RED}Errors:{Colors.END}")
                for error in self.errors:
                    print(f"  - {error}")
            if self.warnings:
                print(f"\n{Colors.YELLOW}Warnings:{Colors.END}")
                for warning in self.warnings:
                    print(f"  - {warning}")

        return all_passed

    def check_version_consistency(self) -> bool:
        """检查版本号一致性"""
        print_section("Version Consistency")

        version_files = {
            "pyproject.toml": self._extract_version_from_pyproject,
            "setup.py": self._extract_version_from_setup,
            "moss/cli_main.py": self._extract_version_from_cli_main,
        }

        versions = {}
        for file, extractor in version_files.items():
            path = self.root / file
            if path.exists():
                try:
                    version = extractor(path)
                    versions[file] = version
                    check_ok(f"{file}: {version}")
                except Exception as e:
                    self.errors.append(f"Failed to extract version from {file}: {e}")
                    check_fail(f"{file}: version extraction failed")
            else:
                self.warnings.append(f"{file} not found")
                check_warn(f"{file}: not found")

        # 检查一致性
        unique_versions = set(versions.values())
        if len(unique_versions) == 1:
            check_ok(f"All versions consistent: {list(unique_versions)[0]}")
            return True
        else:
            check_fail(f"Version mismatch: {versions}")
            return False

    def _extract_version_from_pyproject(self, path: Path) -> str:
        with open(path) as f:
            for line in f:
                if line.startswith("version"):
                    return line.split("=")[1].strip().strip('"')
        raise ValueError("Version not found")

    def _extract_version_from_setup(self, path: Path) -> str:
        with open(path) as f:
            for line in f:
                if 'version=' in line or 'version =' in line:
                    return line.split("=")[1].strip().strip('",')
        raise ValueError("Version not found")

    def _extract_version_from_cli_main(self, path: Path) -> str:
        with open(path) as f:
            content = f.read()
            # Look for version in argparse version argument
            if 'version="MOSS v9.3.0"' in content:
                return "9.3.0"
            # Fallback: look for any 9.3.0 reference
            if '"9.3.0"' in content or "'9.3.0'" in content:
                return "9.3.0"
        raise ValueError("Version not found in cli_main.py")

    def check_file_structure(self) -> bool:
        """检查文件结构"""
        print_section("File Structure")

        required_files = [
            "pyproject.toml",
            "setup.py",
            "README.md",
            "LICENSE",
            "moss/__init__.py",
            "moss/core/__init__.py",
            "moss/cli.py",
        ]

        required_dirs = [
            "moss/core",
            "moss/extensions/vscode-moss",
            "moss/extensions/pycharm-moss",
            "moss/ci",
        ]

        all_ok = True

        for file in required_files:
            path = self.root / file
            if path.exists():
                check_ok(f"{file} exists")
            else:
                check_fail(f"{file} missing")
                self.errors.append(f"Required file missing: {file}")
                all_ok = False

        for dir in required_dirs:
            path = self.root / dir
            if path.exists() and path.is_dir():
                check_ok(f"{dir}/ exists")
            else:
                check_warn(f"{dir}/ missing (optional)")

        return all_ok

    def check_imports(self) -> bool:
        """检查关键导入"""
        print_section("Import Checks")

        imports_to_check = [
            ("moss.core", "PerformanceEngine"),
            ("moss.core", "IncrementalAnalyzer"),
            ("moss.core", "ParallelAnalyzer"),
            ("moss.core", "MossAnalysisProvider"),
            ("moss.core", "RefactoringRecommender"),
            ("moss.core", "PatternLearningEngine"),
            ("moss.core", "TeamManager"),
        ]

        all_ok = True
        for module, name in imports_to_check:
            try:
                exec(f"from {module} import {name}")
                check_ok(f"from {module} import {name}")
            except Exception as e:
                check_fail(f"from {module} import {name}: {e}")
                self.errors.append(f"Import failed: {module}.{name}")
                all_ok = False

        return all_ok

    def check_cli_entry_point(self) -> bool:
        """检查 CLI 入口点"""
        print_section("CLI Entry Point")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "moss.cli", "--version"],
                capture_output=True,
                text=True,
                cwd=self.root
            )
            if result.returncode == 0 and "9.3.0" in result.stdout:
                check_ok(f"CLI version: {result.stdout.strip()}")
                return True
            else:
                check_fail(f"CLI check failed: {result.stderr}")
                return False
        except Exception as e:
            check_fail(f"CLI check error: {e}")
            return False

    def check_documentation(self) -> bool:
        """检查文档"""
        print_section("Documentation")

        docs_to_check = [
            "README.md",
            "docs/v9.3.0_roadmap.md",
            "docs/v9.3.0_phase1_summary.md",
            "RELEASE_v9.3.0.md",
        ]

        all_ok = True
        for doc in docs_to_check:
            path = self.root / doc
            if path.exists():
                size = path.stat().st_size
                check_ok(f"{doc} ({size} bytes)")
            else:
                check_warn(f"{doc} missing")

        return all_ok

    def check_tests(self) -> bool:
        """检查测试"""
        print_section("Tests")

        test_dir = self.root / "tests"
        if test_dir.exists():
            test_files = list(test_dir.glob("test_*.py"))
            check_ok(f"Found {len(test_files)} test files")
            return True
        else:
            check_warn("tests/ directory not found (optional for release)")
            return True

    def check_ci_cd_files(self) -> bool:
        """检查 CI/CD 文件"""
        print_section("CI/CD Files")

        ci_files = [
            "ci/action.yml",
            "ci/github-workflow.yml",
            "ci/gitlab-ci.yml",
            "ci/pre-commit-hooks.yaml",
        ]

        all_ok = True
        for file in ci_files:
            path = self.root / file
            if path.exists():
                check_ok(f"{file} exists")
            else:
                check_warn(f"{file} missing")

        return all_ok


def main():
    checker = ReleaseChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
