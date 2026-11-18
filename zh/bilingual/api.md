# 双语对照：API 参考

> 本页为 `api.md` 的中英段落对照（DR-005 独立对照模式）。每段先中文译文，再以引用块给出英文原文；代码块为逐字保留内容，不参与对照。

## API 参考

> 原文标题：API Reference

{fmt} 库 API 由以下组件构成：

```text
The {fmt} library API consists of the following components:
```

- [`fmt/core.h`](#core-api)：核心 API，为 `char`/UTF-8 提供主要格式化
  函数，支持 C++20 编译时检查，包含依赖极少
- [`fmt/format.h`](#format-api)：`fmt::format` 及其他格式化函数，
  以及区域设置支持
- [`fmt/ranges.h`](#ranges-api)：范围与元组的格式化
- [`fmt/chrono.h`](#chrono-api)：日期与时间格式化
- [`fmt/std.h`](#std-api)：标准库类型的格式化器
- [`fmt/enum.h`](#enum-api)：注解枚举的格式化
- [`fmt/compile.h`](#compile-api)：格式字符串编译
- [`fmt/color.h`](#color-api)：终端颜色与文本样式
- [`fmt/os.h`](#os-api)：系统 API
- [`fmt/ostream.h`](#ostream-api)：`std::ostream` 支持
- [`fmt/args.h`](#args-api)：动态参数列表
- [`fmt/printf.h`](#printf-api)：安全的 `printf`
- [`fmt/xchar.h`](#xchar-api)：可选的 `wchar_t` 支持

```text
- [`fmt/core.h`](#core-api): the core API providing main formatting functions
  for `char`/UTF-8 with C++20 compile-time checks and minimal dependencies
- [`fmt/format.h`](#format-api): `fmt::format` and other formatting functions
  as well as locale support
- [`fmt/ranges.h`](#ranges-api): formatting of ranges and tuples
- [`fmt/chrono.h`](#chrono-api): date and time formatting
- [`fmt/std.h`](#std-api): formatters for standard library types
- [`fmt/enum.h`](#enum-api): formatting of annotated enums
- [`fmt/compile.h`](#compile-api): format string compilation
- [`fmt/color.h`](#color-api): terminal colors and text styles
- [`fmt/os.h`](#os-api): system APIs
- [`fmt/ostream.h`](#ostream-api): `std::ostream` support
- [`fmt/args.h`](#args-api): dynamic argument lists
- [`fmt/printf.h`](#printf-api): safe `printf`
- [`fmt/xchar.h`](#xchar-api): optional `wchar_t` support
```

库提供的所有函数与类型均位于命名空间 `fmt`
中，宏以 `FMT_` 为前缀。

```text
All functions and types provided by the library reside in namespace `fmt`
and macros have prefix `FMT_`.
```

## C++ 模块 API

> 原文标题：C++ Module API

使用 C++ 模块 API 时，无需包含上面列出的头文件，可改用
`import fmt;` 语句。下列其余功能保持不变。

```text
With the C++ module API, the headers listed above don't need to be included.
You can use the `import fmt;` statement instead. All other functionality,
listed below, remains the same.
```

## 核心 API

> 原文标题：Core API

`fmt/core.h` 定义核心 API，为 `char`/UTF-8 提供主要格式化函数，
支持 C++20 编译时检查。它的头文件包含依赖极少，编译速度更快。
该头文件仅在以库方式使用 {fmt}（默认方式）时才有收益，
在仅头文件模式下无此优势。它还为以下类型提供 `formatter` 特化：

```text
`fmt/core.h` defines the core API which provides main formatting functions
for `char`/UTF-8 with C++20 compile-time checks. It has minimal include
dependencies for better compile times. This header is only beneficial when
using {fmt} as a library (the default) and not in the header-only mode.
It also provides `formatter` specializations for the following types:
```

- `int`, `long long`
- `unsigned`, `unsigned long long`
- `float`, `double`, `long double`
- `bool`
- `char`
- `const char*`, [`fmt::string_view`](#basic_string_view)
- `const void*`

```text
- `int`, `long long`
- `unsigned`, `unsigned long long`
- `float`, `double`, `long double`
- `bool`
- `char`
- `const char*`, [`fmt::string_view`](#basic_string_view)
- `const void*`
```

以下函数使用与 Python 中
[str.format](https://docs.python.org/3/library/stdtypes.html#str.format)
类似的[格式字符串语法](syntax.md)。它们接受 *fmt* 与 *args* 作为参数。

```text
The following functions use [format string syntax](syntax.md) similar to that
of [str.format](https://docs.python.org/3/library/stdtypes.html#str.format)
in Python. They take *fmt* and *args* as arguments.
```

*fmt* 是格式字符串，包含字面文本以及由花括号 `{}` 界定的替换字段。
这些字段在结果字符串中被替换为格式化后的参数。
[`fmt::format_string`](#format_string) 是一种格式字符串，可从字符串
字面量或 `constexpr` 字符串隐式构造，并在 C++20 下于编译时检查。
若要传入运行时格式字符串，请用 [`fmt::runtime`](#runtime) 包装。

```text
*fmt* is a format string that contains literal text and replacement fields
surrounded by braces `{}`. The fields are replaced with formatted arguments
in the resulting string. [`fmt::format_string`](#format_string) is a format
string which can be implicitly constructed from a string literal or a
`constexpr` string and is checked at compile time in C++20. To pass a runtime
format string wrap it in [`fmt::runtime`](#runtime).
```

*args* 是参数列表，表示待格式化的对象。

```text
*args* is an argument list representing objects to be formatted.
```

除非另有说明，I/O 错误将以 [`std::system_error`](
https://en.cppreference.com/w/cpp/error/system_error) 异常的形式报告。

```text
I/O errors are reported as [`std::system_error`](
https://en.cppreference.com/w/cpp/error/system_error) exceptions unless
specified otherwise.
```

::: print(format_string<T...>, T&&...)

```text
::: print(format_string<T...>, T&&...)
```

::: print(FILE*, format_string<T...>, T&&...)

```text
::: print(FILE*, format_string<T...>, T&&...)
```

::: println(format_string<T...>, T&&...)

```text
::: println(format_string<T...>, T&&...)
```

::: println(FILE*, format_string<T...>, T&&...)

```text
::: println(FILE*, format_string<T...>, T&&...)
```

::: format_to(OutputIt&&, format_string<T...>, T&&...)

```text
::: format_to(OutputIt&&, format_string<T...>, T&&...)
```

::: format_to_n(OutputIt, size_t, format_string<T...>, T&&...)

```text
::: format_to_n(OutputIt, size_t, format_string<T...>, T&&...)
```

::: format_to_n_result

```text
::: format_to_n_result
```

::: formatted_size(format_string<T...>, T&&...)

```text
::: formatted_size(format_string<T...>, T&&...)
```

<a id="udt"></a>
### 格式化用户定义类型

```text
<a id="udt"></a>
### Formatting User-Defined Types
```

{fmt} 库为许多标准 C++ 类型提供格式化器。
范围与元组（含 `std::vector` 等标准容器）见
[`fmt/ranges.h`](#ranges-api)，日期与时间格式化见
[`fmt/chrono.h`](#chrono-api)，其他标准库类型见
[`fmt/std.h`](#std-api)。

```text
The {fmt} library provides formatters for many standard C++ types.
See [`fmt/ranges.h`](#ranges-api) for ranges and tuples including standard
containers such as `std::vector`, [`fmt/chrono.h`](#chrono-api) for date and
time formatting and [`fmt/std.h`](#std-api) for other standard library types.
```

让用户定义类型可格式化有两种方式：提供 `format_as` 函数，
或特化 `formatter` 结构模板。非 void 指针类型被有意禁止格式化，
无法通过任一扩展 API 使其可格式化。

```text
There are two ways to make a user-defined type formattable: providing a
`format_as` function or specializing the `formatter` struct template.
Formatting of non-void pointer types is intentionally disallowed and they
cannot be made formattable via either extension API.
```

若希望您的类型以与另一类型相同的格式说明符进行格式化，
请使用 `format_as`。`format_as` 函数应接受您的类型的一个对象，
并返回某个可格式化类型的对象，且应定义在与您的类型相同的
命名空间中。当类型同时匹配另一个 `formatter` 特化（如范围
`formatter`）时不能使用 `format_as`，因为特化会产生歧义。
如可能，请禁用冲突的特化，或改为提供显式的 `formatter` 特化。

```text
Use `format_as` if you want to make your type formattable as some other
type with the same format specifiers. The `format_as` function should
take an object of your type and return an object of a formattable type.
It should be defined in the same namespace as your type.
`format_as` cannot be used when a type also matches another `formatter`
specialization, such as the range `formatter`, because the specializations
would be ambiguous. Disable the conflicting specialization, if possible,
or provide an explicit `formatter` specialization instead.
```

示例（[在线运行](https://godbolt.org/z/nvME4arz8)）：

```text
Example ([run](https://godbolt.org/z/nvME4arz8)):
```

## #include <fmt/format.h>

> 原文标题：#include <fmt/format.h>

    namespace kevin_namespacy {

```text
    namespace kevin_namespacy {
```

    enum class film {
      house_of_cards, american_beauty, se7en = 7
    };

```text
    enum class film {
      house_of_cards, american_beauty, se7en = 7
    };
```

    auto format_as(film f) { return fmt::underlying(f); }

```text
    auto format_as(film f) { return fmt::underlying(f); }
```

    }

```text
    }
```

    int main() {
      fmt::print("{}\n", kevin_namespacy::film::se7en); // Output: 7
    }

```text
    int main() {
      fmt::print("{}\n", kevin_namespacy::film::se7en); // Output: 7
    }
```

使用特化更复杂，但可完全控制解析与格式化。采用此方式时，
请为您的类型特化 `formatter` 结构模板，并实现 `parse` 与
`format` 方法。

```text
Using a specialization is more complex, but gives you full control over
parsing and formatting. To use this method, specialize the `formatter`
struct template for your type and implement `parse` and `format`
methods.
```

推荐的定义格式化器的方式是通过继承或组合复用现有格式化器。
这样无需自行实现即可支持标准格式说明符。例如：

```text
The recommended way of defining a formatter is by reusing an existing
one via inheritance or composition. This way you can support standard
format specifiers without implementing them yourself. For example:
```

注意 `formatter<string_view>::format` 定义于 `fmt/format.h`，
因此源文件必须包含它。由于 `parse` 继承自
`formatter<string_view>`，它将识别所有字符串格式规范，例如

```text
Note that `formatter<string_view>::format` is defined in `fmt/format.h`
so it has to be included in the source file. Since `parse` is inherited
from `formatter<string_view>` it will recognize all string format
specifications, for example
```

将返回 `"      blue"`。

```text
will return `"      blue"`.
```

<!-- The experimental `nested_formatter` provides an easy way of applying a
formatter to one or more subobjects.

```text
<!-- The experimental `nested_formatter` provides an easy way of applying a
formatter to one or more subobjects.
```

For example:

```text
For example:
```

## #include <fmt/format.h>

> 原文标题：#include <fmt/format.h>

    struct point {
      double x, y;
    };

```text
    struct point {
      double x, y;
    };
```

    template <>
    struct fmt::formatter<point> : nested_formatter<double> {
      auto format(point p, format_context& ctx) const {
        return write(ctx, "(", nested(p.x), ", ", nested(p.y), ")");
      }
    };

```text
    template <>
    struct fmt::formatter<point> : nested_formatter<double> {
      auto format(point p, format_context& ctx) const {
        return write(ctx, "(", nested(p.x), ", ", nested(p.y), ")");
      }
    };
```

    int main() {
      fmt::print("[{:>20.2f}]", point{1, 2});
    }

```text
    int main() {
      fmt::print("[{:>20.2f}]", point{1, 2});
    }
```

prints:

```text
prints:
```

    [          (1.00, 2.00)]

```text
    [          (1.00, 2.00)]
```

Notice that fill, align and width are applied to the whole object which
is the recommended behavior while the remaining specifiers apply to
elements. -->

```text
Notice that fill, align and width are applied to the whole object which
is the recommended behavior while the remaining specifiers apply to
elements. -->
```

一般而言，格式化器具有如下形式：

```text
In general the formatter has the following form:
```

    template <> struct fmt::formatter<T> {
      // Parses format specifiers and stores them in the formatter.
      //
      // [ctx.begin(), ctx.end()) is a, possibly empty, character range that
      // contains a part of the format string starting from the format
      // specifications to be parsed, e.g. in
      //
      //   fmt::format("{:f} continued", ...);
      //
      // the range will contain "f} continued". The formatter should parse
      // specifiers until '}' or the end of the range. In this example the
      // formatter should parse the 'f' specifier and return an iterator
      // pointing to '}'.
      constexpr auto parse(format_parse_context& ctx)
        -> format_parse_context::iterator;

```text
    template <> struct fmt::formatter<T> {
      // Parses format specifiers and stores them in the formatter.
      //
      // [ctx.begin(), ctx.end()) is a, possibly empty, character range that
      // contains a part of the format string starting from the format
      // specifications to be parsed, e.g. in
      //
      //   fmt::format("{:f} continued", ...);
      //
      // the range will contain "f} continued". The formatter should parse
      // specifiers until '}' or the end of the range. In this example the
      // formatter should parse the 'f' specifier and return an iterator
      // pointing to '}'.
      constexpr auto parse(format_parse_context& ctx)
        -> format_parse_context::iterator;
```

      // Formats value using the parsed format specification stored in this
      // formatter and writes the output to ctx.out().
      auto format(const T& value, format_context& ctx) const
        -> format_context::iterator;
    };

```text
      // Formats value using the parsed format specification stored in this
      // formatter and writes the output to ctx.out().
      auto format(const T& value, format_context& ctx) const
        -> format_context::iterator;
    };
```

建议至少支持作用于整个对象的填充、对齐与宽度，
其语义与标准格式化器一致。

```text
It is recommended to at least support fill, align and width that apply
to the whole object and have the same semantics as in standard
formatters.
```

您还可以为类层次结构编写格式化器：

```text
You can also write a formatter for a hierarchy of classes:
```

不允许同时提供 `formatter` 特化与 `format_as` 重载。

```text
Providing both a `formatter` specialization and a `format_as` overload is
disallowed.
```

::: basic_format_parse_context

```text
::: basic_format_parse_context
```

::: context

```text
::: context
```

::: format_context

```text
::: format_context
```

## 编译时检查

> 原文标题：Compile-Time Checks

在支持 C++20 `consteval` 的编译器上，格式字符串的编译时检查
默认启用。较旧的编译器可改用 `fmt/format.h` 中定义的
[FMT_STRING](#legacy-checks) 宏。

```text
Compile-time format string checks are enabled by default on compilers
that support C++20 `consteval`. On older compilers you can use the
[FMT_STRING](#legacy-checks) macro defined in `fmt/format.h` instead.
```

与 Python 的 `str.format` 及普通函数一样，
允许存在未使用的参数。

```text
Unused arguments are allowed as in Python's `str.format` and ordinary functions.
```

如何在自有函数中借助 `fmt::format_string` 启用编译时检查
并避免模板膨胀，参见[类型擦除](#type-erasure)一节示例。

```text
See [Type Erasure](#type-erasure) for an example of how to enable compile-time
checks in your own functions with `fmt::format_string` while avoiding template
bloat.
```

::: fstring

```text
::: fstring
```

::: format_string

```text
::: format_string
```

::: runtime(string_view)

```text
::: runtime(string_view)
```

## 类型擦除

> 原文标题：Type Erasure

您可以创建兼具编译时检查与小二进制体积的自有格式化函数，
例如（[在线运行](https://godbolt.org/z/b9Pbasvzc)）：

```text
You can create your own formatting function with compile-time checks and
small binary footprint, for example ([run](https://godbolt.org/z/b9Pbasvzc)):
```

注意 `vlog` 不对参数类型参数化，与完全参数化的版本相比，
这可缩短编译时间并减小二进制代码体积。

```text
Note that `vlog` is not parameterized on argument types which improves
compile times and reduces binary code size compared to a fully
parameterized version.
```

::: make_format_args(T&...)

```text
::: make_format_args(T&...)
```

::: basic_format_args

```text
::: basic_format_args
```

::: format_args

```text
::: format_args
```

::: basic_format_arg

```text
::: basic_format_arg
```

## 命名参数

> 原文标题：Named Arguments

::: arg(const char*, const T&)

```text
::: arg(const char*, const T&)
```

## 兼容性

> 原文标题：Compatibility

::: basic_string_view

```text
::: basic_string_view
```

::: string_view

```text
::: string_view
```

## 格式 API

> 原文标题：Format API

`fmt/format.h` 定义完整的格式 API，提供额外的格式化函数与
区域设置支持。

```text
`fmt/format.h` defines the full format API providing additional
formatting functions and locale support.
```

<a id="format"></a>
::: format(format_string<T...>, T&&...)

```text
<a id="format"></a>
::: format(format_string<T...>, T&&...)
```

::: vformat(string_view, format_args)

```text
::: vformat(string_view, format_args)
```

::: operator""_a()

```text
::: operator""_a()
```

## 工具

> 原文标题：Utilities

::: ptr(T)

```text
::: ptr(T)
```

::: underlying(Enum)

```text
::: underlying(Enum)
```

::: to_string(const T&)

```text
::: to_string(const T&)
```

::: group_digits(T)

```text
::: group_digits(T)
```

::: detail::buffer

```text
::: detail::buffer
```

::: basic_memory_buffer

```text
::: basic_memory_buffer
```

## 系统错误

> 原文标题：System Errors

{fmt} 不使用 `errno` 向用户传递错误信息，但它可能调用会设置
`errno` 的系统函数。用户不应假设库函数会保持
`errno` 的值不变。

```text
{fmt} does not use `errno` to communicate errors to the user, but it may
call system functions which set `errno`. Users should not make any
assumptions about the value of `errno` being preserved by library
functions.
```

::: system_error

```text
::: system_error
```

::: format_system_error

```text
::: format_system_error
```

## 自定义分配器

> 原文标题：Custom Allocators

{fmt} 库支持自定义动态内存分配器。自定义分配器类可作为
模板实参传给 [`fmt::basic_memory_buffer`](#basic_memory_buffer)：

```text
The {fmt} library supports custom dynamic memory allocators. A custom
allocator class can be specified as a template argument to
[`fmt::basic_memory_buffer`](#basic_memory_buffer):
```

    using custom_memory_buffer = 
      fmt::basic_memory_buffer<char, fmt::inline_buffer_size, custom_allocator>;

```text
    using custom_memory_buffer = 
      fmt::basic_memory_buffer<char, fmt::inline_buffer_size, custom_allocator>;
```

也可以编写使用自定义分配器的格式化函数：

```text
It is also possible to write a formatting function that uses a custom
allocator:
```

    using custom_string =
      std::basic_string<char, std::char_traits<char>, custom_allocator>;

```text
    using custom_string =
      std::basic_string<char, std::char_traits<char>, custom_allocator>;
```

    auto vformat(custom_allocator alloc, fmt::string_view fmt,
                 fmt::format_args args) -> custom_string {
      auto buf = custom_memory_buffer(alloc);
      fmt::vformat_to(std::back_inserter(buf), fmt, args);
      return custom_string(buf.data(), buf.size(), alloc);
    }

```text
    auto vformat(custom_allocator alloc, fmt::string_view fmt,
                 fmt::format_args args) -> custom_string {
      auto buf = custom_memory_buffer(alloc);
      fmt::vformat_to(std::back_inserter(buf), fmt, args);
      return custom_string(buf.data(), buf.size(), alloc);
    }
```

    template <typename ...Args>
    auto format(custom_allocator alloc, fmt::string_view fmt,
                const Args& ... args) -> custom_string {
      return vformat(alloc, fmt, fmt::make_format_args(args...));
    }

```text
    template <typename ...Args>
    auto format(custom_allocator alloc, fmt::string_view fmt,
                const Args& ... args) -> custom_string {
      return vformat(alloc, fmt, fmt::make_format_args(args...));
    }
```

该分配器仅用于输出容器。对于内置类型与字符串类型，
格式化函数通常不做任何分配；例外是非默认的浮点格式化
偶尔会退回到 `sprintf`。

```text
The allocator will be used for the output container only. Formatting
functions normally don't do any allocations for built-in and string
types except for non-default floating-point formatting that occasionally
falls back on `sprintf`.
```

## 区域设置

> 原文标题：Locale

默认情况下所有格式化均与区域设置无关。使用 `'L'` 格式说明符
可插入区域设置相应的数字分隔字符：

```text
All formatting is locale-independent by default. Use the `'L'` format
specifier to insert the appropriate number separator characters from the
locale:
```

## #include <fmt/format.h>

> 原文标题：#include <fmt/format.h>

## #include <locale>

> 原文标题：#include <locale>

    std::locale::global(std::locale("en_US.UTF-8"));
    auto s = fmt::format("{:L}", 1000000);  // s == "1,000,000"

```text
    std::locale::global(std::locale("en_US.UTF-8"));
    auto s = fmt::format("{:L}", 1000000);  // s == "1,000,000"
```

`fmt/format.h` 提供以下接受 `std::locale` 参数的格式化函数重载。
区域设置类型是模板参数，以避免代价高昂的 `<locale>` 包含。

```text
`fmt/format.h` provides the following overloads of formatting functions
that take `std::locale` as a parameter. The locale type is a template
parameter to avoid the expensive `<locale>` include.
```

::: format(locale_ref, format_string<T...>, T&&...)

```text
::: format(locale_ref, format_string<T...>, T&&...)
```

::: format_to(OutputIt, locale_ref, format_string<T...>, T&&...)

```text
::: format_to(OutputIt, locale_ref, format_string<T...>, T&&...)
```

::: formatted_size(locale_ref, format_string<T...>, T&&...)

```text
::: formatted_size(locale_ref, format_string<T...>, T&&...)
```

<a id="legacy-checks"></a>
### 旧式编译时检查

```text
<a id="legacy-checks"></a>
### Legacy Compile-Time Checks
```

`FMT_STRING` 在较旧的编译器上启用编译时检查。它要求
C++14 或更高版本，在 C++11 中是空操作。

```text
`FMT_STRING` enables compile-time checks on older compilers. It requires
C++14 or later and is a no-op in C++11.
```

::: FMT_STRING

```text
::: FMT_STRING
```

要强制使用旧式编译时检查，请定义预处理器变量
`FMT_ENFORCE_COMPILE_STRING`。设置后，接受 `FMT_STRING`
的函数在遇到普通字符串时将编译失败。

```text
To force the use of legacy compile-time checks, define the preprocessor
variable `FMT_ENFORCE_COMPILE_STRING`. When set, functions accepting
`FMT_STRING` will fail to compile with regular strings.
```

<a id="ranges-api"></a>
## 范围与元组格式化

```text
<a id="ranges-api"></a>
## Range and Tuple Formatting
```

`fmt/ranges.h` 为范围与元组提供格式化支持：

```text
`fmt/ranges.h` provides formatting support for ranges and tuples:
```

## #include <fmt/ranges.h>

> 原文标题：#include <fmt/ranges.h>

    fmt::print("{}", std::tuple<char, int>{'a', 42});
    // Output: ('a', 42)

```text
    fmt::print("{}", std::tuple<char, int>{'a', 42});
    // Output: ('a', 42)
```

借助 `fmt::join`，可用自定义分隔符分隔元组元素：

```text
Using `fmt::join`, you can separate tuple elements with a custom separator:
```

## #include <fmt/ranges.h>

> 原文标题：#include <fmt/ranges.h>

    auto t = std::tuple<int, char>{1, 'a'};
    fmt::print("{}", fmt::join(t, ", "));
    // Output: 1, a

```text
    auto t = std::tuple<int, char>{1, 'a'};
    fmt::print("{}", fmt::join(t, ", "));
    // Output: 1, a
```

::: join(Range&&, string_view)

```text
::: join(Range&&, string_view)
```

::: join(It, Sentinel, string_view)

```text
::: join(It, Sentinel, string_view)
```

::: join(std::initializer_list<T>, string_view)

```text
::: join(std::initializer_list<T>, string_view)
```

<a id="chrono-api"></a>
## 日期与时间格式化

```text
<a id="chrono-api"></a>
## Date and Time Formatting
```

`fmt/chrono.h` 为以下类型提供格式化器：

```text
`fmt/chrono.h` provides formatters for
```

- [`std::chrono::duration`](https://en.cppreference.com/w/cpp/chrono/duration)
- [`std::chrono::time_point`](
  https://en.cppreference.com/w/cpp/chrono/time_point)
- [`std::tm`](https://en.cppreference.com/w/cpp/chrono/c/tm)

```text
- [`std::chrono::duration`](https://en.cppreference.com/w/cpp/chrono/duration)
- [`std::chrono::time_point`](
  https://en.cppreference.com/w/cpp/chrono/time_point)
- [`std::tm`](https://en.cppreference.com/w/cpp/chrono/c/tm)
```

格式语法见[时间日期格式规范](syntax.md#
chrono-format-spec)。

```text
The format syntax is described in [Chrono Format Specifications](syntax.md#
chrono-format-spec).
```

**示例**：

```text
**Example**:
```

## #include <fmt/chrono.h>

> 原文标题：#include <fmt/chrono.h>

    int main() {
      auto now = std::chrono::system_clock::now();

```text
    int main() {
      auto now = std::chrono::system_clock::now();
```

      fmt::print("The date is {:%Y-%m-%d}.\n", now);
      // Output: The date is 2020-11-07.
      // (with 2020-11-07 replaced by the current date)

```text
      fmt::print("The date is {:%Y-%m-%d}.\n", now);
      // Output: The date is 2020-11-07.
      // (with 2020-11-07 replaced by the current date)
```

      using namespace std::literals::chrono_literals;

```text
      using namespace std::literals::chrono_literals;
```

      fmt::print("Default format: {} {}\n", 42s, 100ms);
      // Output: Default format: 42s 100ms

```text
      fmt::print("Default format: {} {}\n", 42s, 100ms);
      // Output: Default format: 42s 100ms
```

      fmt::print("strftime-like format: {:%H:%M:%S}\n", 3h + 15min + 30s);
      // Output: strftime-like format: 03:15:30
    }

```text
      fmt::print("strftime-like format: {:%H:%M:%S}\n", 3h + 15min + 30s);
      // Output: strftime-like format: 03:15:30
    }
```

::: gmtime(std::time_t)

```text
::: gmtime(std::time_t)
```

<a id="std-api"></a>
## 标准库类型格式化

```text
<a id="std-api"></a>
## Standard Library Types Formatting
```

`fmt/std.h` 为以下类型提供格式化器：

```text
`fmt/std.h` provides formatters for:
```

- [`std::atomic`](https://en.cppreference.com/w/cpp/atomic/atomic)
- [`std::atomic_flag`](https://en.cppreference.com/w/cpp/atomic/atomic_flag)
- [`std::bitset`](https://en.cppreference.com/w/cpp/utility/bitset)
- [`std::error_code`](https://en.cppreference.com/w/cpp/error/error_code)
- [`std::exception`](https://en.cppreference.com/w/cpp/error/exception)
- [`std::filesystem::path`](https://en.cppreference.com/w/cpp/filesystem/path)
- [`std::monostate`](
  https://en.cppreference.com/w/cpp/utility/variant/monostate)
- [`std::optional`](https://en.cppreference.com/w/cpp/utility/optional)
- [`std::source_location`](
  https://en.cppreference.com/w/cpp/utility/source_location)
- [`std::thread::id`](https://en.cppreference.com/w/cpp/thread/thread/id)
- [`std::variant`](https://en.cppreference.com/w/cpp/utility/variant/variant)

```text
- [`std::atomic`](https://en.cppreference.com/w/cpp/atomic/atomic)
- [`std::atomic_flag`](https://en.cppreference.com/w/cpp/atomic/atomic_flag)
- [`std::bitset`](https://en.cppreference.com/w/cpp/utility/bitset)
- [`std::error_code`](https://en.cppreference.com/w/cpp/error/error_code)
- [`std::exception`](https://en.cppreference.com/w/cpp/error/exception)
- [`std::filesystem::path`](https://en.cppreference.com/w/cpp/filesystem/path)
- [`std::monostate`](
  https://en.cppreference.com/w/cpp/utility/variant/monostate)
- [`std::optional`](https://en.cppreference.com/w/cpp/utility/optional)
- [`std::source_location`](
  https://en.cppreference.com/w/cpp/utility/source_location)
- [`std::thread::id`](https://en.cppreference.com/w/cpp/thread/thread/id)
- [`std::variant`](https://en.cppreference.com/w/cpp/utility/variant/variant)
```

::: ptr(const std::unique_ptr<T, Deleter>&)

```text
::: ptr(const std::unique_ptr<T, Deleter>&)
```

::: ptr(const std::shared_ptr<T>&)

```text
::: ptr(const std::shared_ptr<T>&)
```

## 变体

> 原文标题：Variants

`std::variant` 仅在其每个备选类型都可格式化时才能被格式化，
且需要 `__cpp_lib_variant` [库特性](https://en.cppreference.com/w/cpp/feature_test)。

```text
A `std::variant` can be formatted only if every alternative is
formattable, and requires the `__cpp_lib_variant` [library
feature](https://en.cppreference.com/w/cpp/feature_test).
```

**示例**：

```text
**Example**:
```

## #include <fmt/std.h>

> 原文标题：#include <fmt/std.h>

    fmt::print("{}", std::variant<char, float>('x'));
    // Output: variant('x')

```text
    fmt::print("{}", std::variant<char, float>('x'));
    // Output: variant('x')
```

    fmt::print("{}", std::variant<std::monostate, char>());
    // Output: variant(monostate)

```text
    fmt::print("{}", std::variant<std::monostate, char>());
    // Output: variant(monostate)
```

## 位域与紧凑结构体

> 原文标题：Bit-Fields and Packed Structs

要格式化位域，或应用了 `__attribute__((packed))` 的结构体字段，
需通过强制转换或一元 `+` 将其转换为底层或兼容类型
（[godbolt](https://www.godbolt.org/z/3qKKs6T5Y)）：

```text
To format a bit-field or a field of a struct with `__attribute__((packed))`
applied to it, you need to convert it to the underlying or compatible type via
a cast or a unary `+` ([godbolt](https://www.godbolt.org/z/3qKKs6T5Y)):
```

这是 C++ 中"完美"转发的一个已知局限。

```text
This is a known limitation of "perfect" forwarding in C++.
```

<a id="enum-api"></a>
## 枚举格式化

```text
<a id="enum-api"></a>
## Enum Formatting
```

`fmt/enum.h` 提供对以 `fmt::as_identifiers` 注解的枚举的格式化。
此类枚举会格式化为与被格式化值匹配的枚举项的标识符：

```text
`fmt/enum.h` provides formatting of enums annotated with
`fmt::as_identifiers`. Such an enum is formatted as the identifier of the
enumerator matching the formatted value:
```

## #include <fmt/enum.h>

> 原文标题：#include <fmt/enum.h>

    enum class [[=fmt::as_identifiers]] color { red, green, blue };

```text
    enum class [[=fmt::as_identifiers]] color { red, green, blue };
```

    fmt::print("{}", color::green);
    // Output: green

```text
    fmt::print("{}", color::green);
    // Output: green
```

此类枚举使用字符串[格式规范](
syntax.md#format-specification)格式化，例如：

```text
Such enums are formatted using the string [Format Specification](
syntax.md#format-specification), for example:
```

    fmt::print("[{:>7}]", color::red);
    // Output: [    red]

```text
    fmt::print("[{:>7}]", color::red);
    // Output: [    red]
```

标识符仅以 `char` 字符串形式提供，因此注解枚举无法用
其他字符类型格式化。

```text
Identifiers are only available as `char` strings so annotated enums are not
formattable with other character types.
```

若多个枚举项具有相同值，则按声明顺序取第一个。
未匹配任何枚举项的值会先以十进制底层值表示，
再应用字符串格式化：

```text
If several enumerators have the same value, the first one in the order of
declaration is used. A value that doesn't match any enumerator is represented
as its underlying value in decimal before applying string formatting:
```

    fmt::print("{}", static_cast<color>(42));
    // Output: 42

```text
    fmt::print("{}", static_cast<color>(42));
    // Output: 42
```

以 `fmt::as_underlying` 注解的枚举则使用整数[格式规范](
syntax.md#format-specification)格式化为底层值：

```text
An enum annotated with `fmt::as_underlying` is instead formatted as its
underlying value using the integer [Format Specification](
syntax.md#format-specification):
```

    enum class [[=fmt::as_underlying]] color { red = 1, green = 2, blue = 4 };

```text
    enum class [[=fmt::as_underlying]] color { red = 1, green = 2, blue = 4 };
```

    fmt::print("{:04x}", color::blue);
    // Output: 0004

```text
    fmt::print("{:04x}", color::blue);
    // Output: 0004
```

此类枚举在类型擦除前被映射到底层类型，因此还可用作
动态宽度或精度。与 `fmt::as_identifiers` 不同，
它适用于所有字符类型。两种注解指定不同的表示形式，
不能组合使用。

```text
Such an enum is mapped to its underlying type before type erasure, so it can
also be used as dynamic width or precision. Unlike `fmt::as_identifiers`, it
works with all character types. The two annotations specify different
representations and cannot be combined.
```

未注解的枚举不受影响，仍按原方式格式化——即限定作用域的
枚举需要 `format_as` 或 `formatter` 特化，见
[格式化用户定义类型](#udt)。

```text
Enums without an annotation are not affected and are formatted as before, i.e.
scoped enums require `format_as` or a `formatter` specialization, see
[Formatting User-Defined Types](#udt).
```

这利用了两个 C++26 特性：用于获取枚举项标识符的
[反射](https://en.cppreference.com/w/cpp/language/operator_reflection)，
以及用于通过 `fmt::as_identifiers` 将枚举纳入的
[注解](https://en.cppreference.com/w/cpp/language/annotations)。因此需要
支持反射的编译器，GCC 可能需要额外标志如 `-freflection`。宏
`FMT_USE_REFLECTION` 在反射可用时为 1，否则为 0。
用户也可自行定义它以禁用反射。

```text
This uses two C++26 features:
[reflection](https://en.cppreference.com/w/cpp/language/operator_reflection) to
retrieve the enumerator identifiers and
[annotations](https://en.cppreference.com/w/cpp/language/annotations) to opt an
enum in via `fmt::as_identifiers`. It therefore requires a compiler with
reflection support,
which may need an extra flag such as `-freflection` in GCC. The macro
`FMT_USE_REFLECTION` is set to 1 if reflection is available and to 0 otherwise.
It can also be defined by the user to disable the use of reflection.
```

以模块方式构建 {fmt} 时，反射支持在模块自身编译时检测，
因此仅当模块构建时启用了反射，此 API 才对导入方可用。

```text
When {fmt} is built as a module, reflection support is detected when the module
itself is compiled, so this API is only available to importers if the module was
built with reflection enabled.
```

<a id="compile-api"></a>
## 编译时支持

```text
<a id="compile-api"></a>
## Compile-Time Support
```

`fmt/compile.h` 提供格式字符串编译与编译时（`constexpr`）格式化，
通过 `FMT_COMPILE` 宏或命名空间 `fmt::literals` 中定义的 `_cf`
用户定义字面量启用。以 `FMT_COMPILE` 或 `_cf` 标记的格式字符串
会在编译时被解析、检查并转换为高效格式化代码。它支持内置与
字符串类型参数，也支持在 `formatter` 特化中 `format` 方法以
格式上下文类型为模板参数的用户定义类型。
例如（[在线运行](https://www.godbolt.org/z/3c13erEoq)）：

```text
`fmt/compile.h` provides format string compilation and compile-time
(`constexpr`) formatting enabled via the `FMT_COMPILE` macro or the `_cf`
user-defined literal defined in namespace `fmt::literals`. Format strings
marked with `FMT_COMPILE` or `_cf` are parsed, checked and converted into
efficient formatting code at compile-time. This supports arguments of built-in
and string types as well as user-defined types with `format` methods taking
the format context type as a template parameter in their `formatter`
specializations. For example ([run](https://www.godbolt.org/z/3c13erEoq)):
```

    struct point {
      double x;
      double y;
    };

```text
    struct point {
      double x;
      double y;
    };
```

    template <> struct fmt::formatter<point> {
      constexpr auto parse(format_parse_context& ctx) { return ctx.begin(); }

```text
    template <> struct fmt::formatter<point> {
      constexpr auto parse(format_parse_context& ctx) { return ctx.begin(); }
```

      template <typename FormatContext>
      auto format(const point& p, FormatContext& ctx) const {
        return format_to(ctx.out(), "({}, {})"_cf, p.x, p.y);
      }
    };

```text
      template <typename FormatContext>
      auto format(const point& p, FormatContext& ctx) const {
        return format_to(ctx.out(), "({}, {})"_cf, p.x, p.y);
      }
    };
```

    using namespace fmt::literals;
    std::string s = fmt::format("{}"_cf, point(4, 2));

```text
    using namespace fmt::literals;
    std::string s = fmt::format("{}"_cf, point(4, 2));
```

与默认 API 相比，格式字符串编译可能生成更多二进制代码，
因此仅建议在格式化为性能瓶颈之处使用。

```text
Format string compilation can generate more binary code compared to the
default API and is only recommended in places where formatting is a
performance bottleneck.
```

同一组 API 还支持在编译时格式化，例如在 `constexpr`
与 `consteval` 函数中。此外还有实验性的
`FMT_STATIC_FORMAT`，可在编译时格式化为尺寸恰好所需的字符串。
编译时格式化适用于具有 `constexpr` `format` 方法的
内置与用户定义格式化器。示例：

```text
The same APIs support formatting at compile time e.g. in `constexpr`
and `consteval` functions. Additionally there is an experimental
`FMT_STATIC_FORMAT` that allows formatting into a string of the exact
required size at compile time. Compile-time formatting works with built-in
and user-defined formatters that have `constexpr` `format` methods.
Example:
```

    template <> struct fmt::formatter<point> {
      constexpr auto parse(format_parse_context& ctx) { return ctx.begin(); }

```text
    template <> struct fmt::formatter<point> {
      constexpr auto parse(format_parse_context& ctx) { return ctx.begin(); }
```

      template <typename FormatContext>
      constexpr auto format(const point& p, FormatContext& ctx) const {
        return format_to(ctx.out(), "({}, {})"_cf, p.x, p.y);
      }
    };

```text
      template <typename FormatContext>
      constexpr auto format(const point& p, FormatContext& ctx) const {
        return format_to(ctx.out(), "({}, {})"_cf, p.x, p.y);
      }
    };
```

    constexpr auto s = FMT_STATIC_FORMAT("{}", point(4, 2));
    const char* cstr = s.c_str(); // Points the static string "(4, 2)".

```text
    constexpr auto s = FMT_STATIC_FORMAT("{}", point(4, 2));
    const char* cstr = s.c_str(); // Points the static string "(4, 2)".
```

::: operator""_cf

```text
::: operator""_cf
```

::: FMT_COMPILE

```text
::: FMT_COMPILE
```

::: FMT_STATIC_FORMAT

```text
::: FMT_STATIC_FORMAT
```

<a id="color-api"></a>
## 终端颜色与文本样式

```text
<a id="color-api"></a>
## Terminal Colors and Text Styles
```

`fmt/color.h` 提供终端颜色与文本样式输出支持。

```text
`fmt/color.h` provides support for terminal color and text style output.
```

::: print(text_style, format_string<T...>, T&&...)

```text
::: print(text_style, format_string<T...>, T&&...)
```

::: fg(detail::color_type)

```text
::: fg(detail::color_type)
```

::: bg(detail::color_type)

```text
::: bg(detail::color_type)
```

::: styled(const T&, text_style)

```text
::: styled(const T&, text_style)
```

<a id="os-api"></a>
## 系统 API

```text
<a id="os-api"></a>
## System APIs
```

::: ostream

```text
::: ostream
```

::: output_file(cstring_view, T...)

```text
::: output_file(cstring_view, T...)
```

::: windows_error

```text
::: windows_error
```

<a id="ostream-api"></a>
## `std::ostream` 支持

```text
<a id="ostream-api"></a>
## `std::ostream` Support
```

`fmt/ostream.h` 提供 `std::ostream` 支持，包括对重载了
插入运算符（`operator<<`）的用户定义类型的格式化。
要使类型可通过 `std::ostream` 格式化，请提供继承自
`ostream_formatter` 的 `formatter` 特化：

```text
`fmt/ostream.h` provides `std::ostream` support including formatting of
user-defined types that have an overloaded insertion operator
(`operator<<`). In order to make a type formattable via `std::ostream`
you should provide a `formatter` specialization inherited from
`ostream_formatter`:
```

## #include <fmt/ostream.h>

> 原文标题：#include <fmt/ostream.h>

    struct date {
      int year, month, day;

```text
    struct date {
      int year, month, day;
```

      friend std::ostream& operator<<(std::ostream& os, const date& d) {
        return os << d.year << '-' << d.month << '-' << d.day;
      }
    };

```text
      friend std::ostream& operator<<(std::ostream& os, const date& d) {
        return os << d.year << '-' << d.month << '-' << d.day;
      }
    };
```

    template <> struct fmt::formatter<date> : ostream_formatter {};

```text
    template <> struct fmt::formatter<date> : ostream_formatter {};
```

    std::string s = fmt::format("The date is {}", date{2012, 12, 9});
    // s == "The date is 2012-12-9"

```text
    std::string s = fmt::format("The date is {}", date{2012, 12, 9});
    // s == "The date is 2012-12-9"
```

::: streamed(const T&)

```text
::: streamed(const T&)
```

::: print(std::ostream&, format_string<T...>, T&&...)

```text
::: print(std::ostream&, format_string<T...>, T&&...)
```

<a id="args-api"></a>
## 动态参数列表

```text
<a id="args-api"></a>
## Dynamic Argument Lists
```

头文件 `fmt/args.h` 提供 `dynamic_format_arg_store`——
一个构建器风格的 API，可用于动态构造格式参数列表。

```text
The header `fmt/args.h` provides `dynamic_format_arg_store`, a builder-like API
that can be used to construct format argument lists dynamically.
```

::: dynamic_format_arg_store

```text
::: dynamic_format_arg_store
```

<a id="printf-api"></a>
## 安全的 `printf`

```text
<a id="printf-api"></a>
## Safe `printf`
```

头文件 `fmt/printf.h` 提供类 `printf` 的格式化功能。
以下函数使用 [printf 格式字符串语法](https://pubs.opengroup.org/onlinepubs/009695399/functions/fprintf.html)
（含位置参数的 POSIX 扩展）。与标准版本不同，
`fmt` 函数是类型安全的：若参数类型与其格式规范不匹配，
将抛出异常。

```text
The header `fmt/printf.h` provides `printf`-like formatting
functionality. The following functions use [printf format string
syntax](https://pubs.opengroup.org/onlinepubs/009695399/functions/fprintf.html)
with the POSIX extension for positional arguments. Unlike their standard
counterparts, the `fmt` functions are type-safe and throw an exception
if an argument type doesn't match its format specification.
```

::: printf(string_view, const T&...)

```text
::: printf(string_view, const T&...)
```

::: fprintf(std::FILE*, string_view, const T&...)

```text
::: fprintf(std::FILE*, string_view, const T&...)
```

::: sprintf(string_view, const T&...)

```text
::: sprintf(string_view, const T&...)
```

<a id="xchar-api"></a>
## 宽字符串

```text
<a id="xchar-api"></a>
## Wide Strings
```

可选头文件 `fmt/xchar.h` 提供 `wchar_t` 与
其他特殊字符类型支持。

```text
The optional header `fmt/xchar.h` provides support for `wchar_t` and
exotic character types.
```

::: wstring_view

```text
::: wstring_view
```

::: wformat_context

```text
::: wformat_context
```

::: to_wstring(const T&)

```text
::: to_wstring(const T&)
```

## 与 C++20 `std::format` 的兼容性

> 原文标题：Compatibility with C++20 `std::format`

{fmt} 实现了几乎全部 [C++20 格式化库](https://en.cppreference.com/w/cpp/utility/format) 功能，
但有以下差异：

```text
{fmt} implements nearly all of the [C++20 formatting
library](https://en.cppreference.com/w/cpp/utility/format) with the
following differences:
```

- 名称定义在 `fmt` 命名空间而非 `std` 中，
  以避免与标准库实现冲突。

```text
- Names are defined in the `fmt` namespace instead of `std` to avoid
  collisions with standard library implementations.
```

- 宽度计算不使用字素簇切分。后者已在单独分支实现，
  但尚未集成。

```text
- Width calculation doesn't use grapheme clusterization. The latter has
  been implemented in a separate branch but hasn't been integrated yet.
```

- {fmt} 的默认浮点表示使用能提供往返保证的最小精度，
  与 Java、Python 等语言类似。`std::format` 目前按
  `std::to_chars` 规定，后者尝试生成最少的字符
  （忽略冗余数字与指数中的符号），可能产生比必要更多的
  十进制数字。

```text
- The default floating-point representation in {fmt} uses the smallest
  precision that provides round-trip guarantees similarly to other languages
  like Java and Python. `std::format` is currently specified in terms of
  `std::to_chars` which tries to generate the smallest number of characters
  (ignoring redundant digits and sign in exponent) and may produce more
  decimal digits than necessary.
```

## 配置选项

> 原文标题：Configuration Options

{fmt} 通过 CMake 选项与预处理器宏提供配置，
用于启用或禁用特性以及优化二进制体积。例如，配置 CMake 时
可用 `-DFMT_OS=OFF` 禁用 `fmt/os.h` 中定义的 OS 相关 API。

```text
{fmt} provides configuration via CMake options and preprocessor macros to
enable or disable features and to optimize for binary size. For example, you
can disable OS-specific APIs defined in `fmt/os.h` with `-DFMT_OS=OFF` when
configuring CMake.
```

## CMake 选项

> 原文标题：CMake Options

- **`FMT_OS`**：设为 `OFF` 时禁用 OS 相关 API（`fmt/os.h`）。
- **`FMT_UNICODE`**：设为 `OFF` 时在
  Windows/MSVC 上禁用 Unicode 支持。其他平台始终启用。

```text
- **`FMT_OS`**: When set to `OFF`, disables OS-specific APIs (`fmt/os.h`).
- **`FMT_UNICODE`**: When set to `OFF`, disables Unicode support on
  Windows/MSVC. Unicode support is always enabled on other platforms.
```

## 宏

> 原文标题：Macros

- **`FMT_HEADER_ONLY`**：定义时启用仅头文件模式。
  是 `fmt::fmt-header-only` CMake 目标的替代方案。
  默认：未定义。

```text
- **`FMT_HEADER_ONLY`**: Enables the header-only mode when defined. It is an
  alternative to using the `fmt::fmt-header-only` CMake target.
  Default: not defined.
```

- **`FMT_USE_EXCEPTIONS`**：设为 `0` 时禁用异常。
  默认：`1`（以 `-fno-exceptions` 编译时为 `0`）。

```text
- **`FMT_USE_EXCEPTIONS`**: Disables the use of exceptions when set to `0`.
  Default: `1` (`0` if compiled with `-fno-exceptions`).
```

- **`FMT_USE_LOCALE`**：设为 `0` 时禁用区域设置支持。
  默认：`1`（`FMT_OPTIMIZE_SIZE > 1` 时为 `0`）。

```text
- **`FMT_USE_LOCALE`**: When set to `0`, disables locale support.
  Default: `1` (`0` when `FMT_OPTIMIZE_SIZE > 1`).
```

- **`FMT_CUSTOM_ASSERT_FAIL`**：设为 `1` 时允许用户提供
  自定义 `fmt::assert_fail` 函数，在断言失败时调用；
  若禁用异常，也在运行时错误时调用。默认：`0`。

```text
- **`FMT_CUSTOM_ASSERT_FAIL`**: When set to `1`, allows users to provide a
  custom `fmt::assert_fail` function which is called on assertion failures and,
  if exceptions are disabled, on runtime errors. Default: `0`.
```

- **`FMT_BUILTIN_TYPES`**：设为 `0` 时禁用对 `int` 之外的
  算术与字符串类型的内置处理。以每次调用开销为代价
  减小库体积。默认：`1`。

```text
- **`FMT_BUILTIN_TYPES`**: When set to `0`, disables built-in handling of
  arithmetic and string types other than `int`. This reduces library size at
  the cost of per-call overhead. Default: `1`.
```

- **`FMT_OPTIMIZE_SIZE`**：控制二进制体积优化：
    - `0` —— 关闭（默认）
    - `1` —— 应用部分优化
    - `2` —— 默认禁用区域设置支持、部分 Unicode 特性与
      命名参数，并应用更激进的优化

```text
- **`FMT_OPTIMIZE_SIZE`**: Controls binary size optimizations:
    - `0` - off (default)
    - `1` - applies some optimizations
    - `2` - disables locale support by default, some Unicode features, and
      named arguments, and applies more aggressive optimizations
```

## 二进制体积优化

> 原文标题：Binary Size Optimization

要以牺牲部分特性为代价将 {fmt} 的二进制体积降到最低，
可使用以下配置：

```text
To minimize the binary footprint of {fmt} as much as possible at the cost of
some features, you can use the following configuration:
```

- CMake 选项：
    - `FMT_OS=OFF`
- 宏：
    - `FMT_BUILTIN_TYPES=0`
    - `FMT_OPTIMIZE_SIZE=2`

```text
- CMake options:
    - `FMT_OS=OFF`
- Macros:
    - `FMT_BUILTIN_TYPES=0`
    - `FMT_OPTIMIZE_SIZE=2`
```

---
*对照段落数：228（代码块未计入）*
