# 快速开始

您可以在 [Compiler Explorer](
https://godbolt.org/z/P7h6cd6o3) 上在线编译并运行 {fmt} 示例。

{fmt} 兼容任何构建系统。下一节介绍其在 CMake 中的用法，其余构建系统见
[构建系统](#build-systems)一节。

## CMake

{fmt} 提供以下 CMake 目标：`fmt::fmt`（标准编译库）、
`fmt::fmt-header-only`（仅头文件库），以及在启用 `FMT_MODULE` 选项时
可选的 `fmt::fmt-module`（C++ 模块库）。推荐使用编译库或模块库
以获得更快的构建速度。

在 CMake 中使用 {fmt} 主要有三种方式：

* **FetchContent**：从 CMake 3.11 开始，您可以使用 [`FetchContent`](
  https://cmake.org/cmake/help/v3.30/module/FetchContent.html) 在配置阶段
  自动下载 {fmt} 作为依赖：

        include(FetchContent)

        FetchContent_Declare(
          fmt
          GIT_REPOSITORY https://github.com/fmtlib/fmt
          GIT_TAG        e69e5f977d458f2650bb346dadf2ad30c5320281) # 10.2.1
        FetchContent_MakeAvailable(fmt)

        target_link_libraries(<your-target> fmt::fmt)

* **已安装**：如果您已[安装](#installation) {fmt}，可在您的
  `CMakeLists.txt` 文件中按如下方式查找并使用：

        find_package(fmt)
        target_link_libraries(<your-target> fmt::fmt)

* **内嵌**：您可以将 {fmt} 源码树加入您的项目，并在
  `CMakeLists.txt` 文件中包含它：

        add_subdirectory(fmt)
        target_link_libraries(<your-target> fmt::fmt)

### 备选目标

如需使用仅头文件目标或模块目标，只需将上述步骤中的
`fmt::fmt` 相应替换为 `fmt::fmt-header-only` 或 `fmt::fmt-module`。

### 使用 C++20 模块

`fmt::fmt-module` 目标仅在启用 `FMT_MODULE` CMake 选项时可用。
在添加 {fmt} 之前配置项目时传入 `-DFMT_MODULE=ON` 即可启用；
或在添加 {fmt} 前将 `CMAKE_CXX_STANDARD` 设为至少 20——若工具链支持，
将自动启用模块支持。

将您的目标链接到 `fmt::fmt-module`，并以导入 `fmt` 取代包含
{fmt} 头文件：

    target_link_libraries(<your-target> PRIVATE fmt::fmt-module)

    import fmt;

    int main() {
      fmt::print("Hello, world!\n");
    }

当使用 CMake 3.28 或更新版本并配合 Ninja 生成器（Ninja 1.11 或更新）、
GCC 15 或 Clang 16（需 `clang-scan-deps`）或更新版本，或
Visual Studio 2022 17.4 或更新版本时，{fmt} 会通过 CMake 原生 C++
模块支持来构建模块。只有以这种带 Ninja 的方式构建时模块才会被安装，
且 CMake 只能在同样使用 Ninja 的项目中导入已安装的模块，
因此请将两者相应配置，例如：

    cmake -G Ninja -DFMT_MODULE=ON ..

在其他工具链下，{fmt} 会退回到直接构建模块的方式，
这适用于 `FetchContent` 和 `add_subdirectory`，但不会安装
`fmt::fmt-module`。该回退方式不适用于 GCC。

## 安装

### Debian/Ubuntu

在 Debian、Ubuntu 或任何其他基于 Debian 的 Linux 发行版上
安装 {fmt}，请使用以下命令：

    apt install libfmt-dev

### Homebrew

在 macOS 上使用 [Homebrew](https://brew.sh/) 安装 {fmt}：

    brew install fmt

### Conda

在 Linux、macOS 和 Windows 上使用 [Conda](
https://docs.conda.io/en/latest/) 安装 {fmt}，采用其 [conda-forge 软件包](
https://github.com/conda-forge/fmt-feedstock)：

    conda install -c conda-forge fmt

### vcpkg

使用 vcpkg 包管理器下载并安装 {fmt}：

    git clone https://github.com/Microsoft/vcpkg.git
    cd vcpkg
    ./bootstrap-vcpkg.sh
    ./vcpkg integrate install
    ./vcpkg install fmt

<!-- The fmt package in vcpkg is kept up to date by Microsoft team members and
community contributors. If the version is out of date, please [create an
issue or pull request](https://github.com/Microsoft/vcpkg) on the vcpkg
repository. -->

### Conan

您可以使用 [Conan](https://conan.io/) 包管理器下载并安装 {fmt}：

    conan install -r conancenter --requires="fmt/[*]" --build=missing

<!-- The {fmt} package in Conan Center is maintained by
[ConanCenterIndex](https://github.com/conan-io/conan-center-index) community.
If the version is out of date or the package does not work,
please create an issue or pull request on the Conan Center Index repository. -->

## 从 `printf` 迁移

[clang-tidy](https://clang.llvm.org/extra/clang-tidy/) v18 提供了
[modernize-use-std-print](https://clang.llvm.org/extra/clang-tidy/checks/modernize/use-std-print.html)
检查项，经配置后可将 `printf` 与
`fprintf` 的调用转换为 `fmt::print`。（默认转换为
`std::print`。）

## 从源码构建

CMake 的工作方式是生成原生 makefile 或工程文件，
供您所选的编译器环境使用。典型工作流程
从以下命令开始：

    mkdir build  # Create a directory to hold the build output.
    cd build
    cmake ..     # Generate native build scripts.

在 `fmt` 仓库根目录下运行。

在类 Unix 系统上，当前目录此时应已生成 Makefile，
随后运行 `make` 即可构建该库。

构建完成后，可运行 `make test` 执行测试。

可通过 `FMT_TEST`
CMake 选项控制是否生成 make `test` 目标。当您将 fmt 作为子目录引入
项目、但不想让 fmt 的测试进入您的 `test` 目标时，
该选项会很有用。

要构建动态库，请将 `BUILD_SHARED_LIBS` CMake 变量设为 `TRUE`：

    cmake -DBUILD_SHARED_LIBS=TRUE ..

要构建带位置无关代码的静态库（例如用于
链接到其他动态库，如 Python 扩展），请将
`CMAKE_POSITION_INDEPENDENT_CODE` CMake 变量设为 `TRUE`：

    cmake -DCMAKE_POSITION_INDEPENDENT_CODE=TRUE ..

构建完成后，在类 Unix 系统上运行 `sudo make install` 即可安装。

### 构建文档

构建文档需要系统中安装以下软件：

- [Python](https://www.python.org/)
- [Doxygen](http://www.stack.nl/~dimitri/doxygen/)
- [MkDocs](https://www.mkdocs.org/)，以及 `mkdocs-material`、`mkdocstrings`、
  `pymdown-extensions` 和 `mike`

先按上一节所述用 CMake 生成 makefile 或工程文件，
然后编译 `doc` 目标/工程，例如：

    make doc

该命令会在 `doc/html` 下生成 HTML 文档。

## 构建系统

### build2

您可以使用 [build2](https://build2.org)（一个依赖管理器兼
构建系统）来使用 {fmt}。

目前该软件包可在以下包仓库中获取：

- <https://cppget.org/fmt/>：已发布的正式版本。
- <https://github.com/build2-packaging/fmt>：未发布或自定义版本。

**用法：**

- `build2` 包名：`fmt`
- 库目标名：`lib{fmt}`

要让您的 `build2` 项目依赖 `fmt`：

- 将下列仓库之一加入您的配置；若尚未添加，
  也可写入 `repositories.manifest`：

        :
        role: prerequisite
        location: https://pkg.cppget.org/1/stable

- 在 `manifest` 文件中添加该包依赖
  （以版本 10 为例）：

        depends: fmt ~10.0.0

- 在相应的 `buildfile` 中导入目标，并将其作为您自己目标的
  前置依赖来使用 `fmt`：

        import fmt = fmt%lib{fmt}
        lib{mylib} : cxx{**} ... $fmt

然后照常使用 `b` 或 `bdep update` 构建项目。

### Meson

[Meson WrapDB](https://mesonbuild.com/Wrapdb-projects.html) 收录了
`fmt`
软件包。

**用法：**

- 运行以下命令从 WrapDB 安装 `fmt`
  子项目：

        meson wrap install fmt

  （在您的项目根目录下执行。）

- 在您项目的 `meson.build` 文件中，
  为新子项目添加条目：

        fmt = subproject('fmt')
        fmt_dep = fmt.get_variable('fmt_dep')

- 包含新的依赖对象以链接 fmt：

        my_build_target = executable(
          'name', 'src/main.cc', dependencies: [fmt_dep])

**选项：**

如有需要，{fmt} 可构建为静态库，
或作为仅头文件库使用。

静态构建请使用以下子项目定义：

    fmt = subproject('fmt', default_options: 'default_library=static')
    fmt_dep = fmt.get_variable('fmt_dep')

仅头文件版本请使用：

    fmt = subproject('fmt', default_options: ['header-only=true'])
    fmt_dep = fmt.get_variable('fmt_header_only_dep')

### Android NDK

{fmt} 提供 [Android.mk 文件](
https://github.com/fmtlib/fmt/blob/master/support/Android.mk)，可用于
配合 [Android NDK](
https://developer.android.com/tools/sdk/ndk/index.html) 构建该库。

### 其他

要将 {fmt} 库用于任何其他构建系统，请将
`include/fmt/core.h`、`include/fmt/format.h`、`include/fmt/format-inl.h`、
`src/format.cc` 以及（可选的）其他头文件从[发布归档](
https://github.com/fmtlib/fmt/releases)或 [git 仓库](
https://github.com/fmtlib/fmt)添加到您的项目中，
将 `include` 加入头文件搜索目录，
并确保 `src/format.cc` 与您的代码一同编译链接。
