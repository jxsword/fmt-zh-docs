# API 参考

{fmt} 库 API 由以下组件构成：

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

库提供的所有函数与类型均位于命名空间 `fmt`
中，宏以 `FMT_` 为前缀。

## C++ 模块 API

使用 C++ 模块 API 时，无需包含上面列出的头文件，可改用
`import fmt;` 语句。下列其余功能保持不变。

## 核心 API

`fmt/core.h` 定义核心 API，为 `char`/UTF-8 提供主要格式化函数，
支持 C++20 编译时检查。它的头文件包含依赖极少，编译速度更快。
该头文件仅在以库方式使用 {fmt}（默认方式）时才有收益，
在仅头文件模式下无此优势。它还为以下类型提供 `formatter` 特化：

- `int`, `long long`
- `unsigned`, `unsigned long long`
- `float`, `double`, `long double`
- `bool`
- `char`
- `const char*`, [`fmt::string_view`](#basic_string_view)
- `const void*`

以下函数使用与 Python 中
[str.format](https://docs.python.org/3/library/stdtypes.html#str.format)
类似的[格式字符串语法](syntax.md)。它们接受 *fmt* 与 *args* 作为参数。

*fmt* 是格式字符串，包含字面文本以及由花括号 `{}` 界定的替换字段。
这些字段在结果字符串中被替换为格式化后的参数。
[`fmt::format_string`](#format_string) 是一种格式字符串，可从字符串
字面量或 `constexpr` 字符串隐式构造，并在 C++20 下于编译时检查。
若要传入运行时格式字符串，请用 [`fmt::runtime`](#runtime) 包装。

*args* 是参数列表，表示待格式化的对象。

除非另有说明，I/O 错误将以 [`std::system_error`](
https://en.cppreference.com/w/cpp/error/system_error) 异常的形式报告。

::: print(format_string<T...>, T&&...)

::: print(FILE*, format_string<T...>, T&&...)

::: println(format_string<T...>, T&&...)

::: println(FILE*, format_string<T...>, T&&...)

::: format_to(OutputIt&&, format_string<T...>, T&&...)

::: format_to_n(OutputIt, size_t, format_string<T...>, T&&...)

::: format_to_n_result

::: formatted_size(format_string<T...>, T&&...)

<a id="udt"></a>
### 格式化用户定义类型

{fmt} 库为许多标准 C++ 类型提供格式化器。
范围与元组（含 `std::vector` 等标准容器）见
[`fmt/ranges.h`](#ranges-api)，日期与时间格式化见
[`fmt/chrono.h`](#chrono-api)，其他标准库类型见
[`fmt/std.h`](#std-api)。

让用户定义类型可格式化有两种方式：提供 `format_as` 函数，
或特化 `formatter` 结构模板。非 void 指针类型被有意禁止格式化，
无法通过任一扩展 API 使其可格式化。

若希望您的类型以与另一类型相同的格式说明符进行格式化，
请使用 `format_as`。`format_as` 函数应接受您的类型的一个对象，
并返回某个可格式化类型的对象，且应定义在与您的类型相同的
命名空间中。当类型同时匹配另一个 `formatter` 特化（如范围
`formatter`）时不能使用 `format_as`，因为特化会产生歧义。
如可能，请禁用冲突的特化，或改为提供显式的 `formatter` 特化。

示例（[在线运行](https://godbolt.org/z/nvME4arz8)）：

    #include <fmt/format.h>

    namespace kevin_namespacy {

    enum class film {
      house_of_cards, american_beauty, se7en = 7
    };

    auto format_as(film f) { return fmt::underlying(f); }

    }

    int main() {
      fmt::print("{}\n", kevin_namespacy::film::se7en); // Output: 7
    }

使用特化更复杂，但可完全控制解析与格式化。采用此方式时，
请为您的类型特化 `formatter` 结构模板，并实现 `parse` 与
`format` 方法。

推荐的定义格式化器的方式是通过继承或组合复用现有格式化器。
这样无需自行实现即可支持标准格式说明符。例如：

```c++
// color.h:
#include <fmt/core.h>

enum class color {red, green, blue};

template <> struct fmt::formatter<color>: formatter<string_view> {
  // parse is inherited from formatter<string_view>.

  auto format(color c, format_context& ctx) const
    -> format_context::iterator;
};
```

```c++
// color.cc:
#include "color.h"
#include <fmt/format.h>

auto fmt::formatter<color>::format(color c, format_context& ctx) const
    -> format_context::iterator {
  string_view name = "unknown";
  switch (c) {
  case color::red:   name = "red"; break;
  case color::green: name = "green"; break;
  case color::blue:  name = "blue"; break;
  }
  return formatter<string_view>::format(name, ctx);
}
```

注意 `formatter<string_view>::format` 定义于 `fmt/format.h`，
因此源文件必须包含它。由于 `parse` 继承自
`formatter<string_view>`，它将识别所有字符串格式规范，例如

```c++
fmt::format("{:>10}", color::blue)
```

将返回 `"      blue"`。

<!-- The experimental `nested_formatter` provides an easy way of applying a
formatter to one or more subobjects.

For example:

    #include <fmt/format.h>

    struct point {
      double x, y;
    };

    template <>
    struct fmt::formatter<point> : nested_formatter<double> {
      auto format(point p, format_context& ctx) const {
        return write(ctx, "(", nested(p.x), ", ", nested(p.y), ")");
      }
    };

    int main() {
      fmt::print("[{:>20.2f}]", point{1, 2});
    }

prints:

    [          (1.00, 2.00)]

Notice that fill, align and width are applied to the whole object which
is the recommended behavior while the remaining specifiers apply to
elements. -->

一般而言，格式化器具有如下形式：

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

      // Formats value using the parsed format specification stored in this
      // formatter and writes the output to ctx.out().
      auto format(const T& value, format_context& ctx) const
        -> format_context::iterator;
    };

建议至少支持作用于整个对象的填充、对齐与宽度，
其语义与标准格式化器一致。

您还可以为类层次结构编写格式化器：

```c++
// demo.h:
#include <type_traits>
#include <fmt/format.h>

struct A {
  virtual ~A() {}
  virtual std::string name() const { return "A"; }
};

struct B : A {
  virtual std::string name() const { return "B"; }
};

template <typename T>
struct fmt::formatter<T, std::enable_if_t<std::is_base_of_v<A, T>, char>> :
    fmt::formatter<std::string> {
  auto format(const A& a, format_context& ctx) const {
    return formatter<std::string>::format(a.name(), ctx);
  }
};
```

```c++
// demo.cc:
#include "demo.h"
#include <fmt/format.h>

int main() {
  B b;
  A& a = b;
  fmt::print("{}", a); // Output: B
}
```

不允许同时提供 `formatter` 特化与 `format_as` 重载。

::: basic_format_parse_context

::: context

::: format_context

### 编译时检查

在支持 C++20 `consteval` 的编译器上，格式字符串的编译时检查
默认启用。较旧的编译器可改用 `fmt/format.h` 中定义的
[FMT_STRING](#legacy-checks) 宏。

与 Python 的 `str.format` 及普通函数一样，
允许存在未使用的参数。

如何在自有函数中借助 `fmt::format_string` 启用编译时检查
并避免模板膨胀，参见[类型擦除](#type-erasure)一节示例。

::: fstring

::: format_string

::: runtime(string_view)

### 类型擦除

您可以创建兼具编译时检查与小二进制体积的自有格式化函数，
例如（[在线运行](https://godbolt.org/z/b9Pbasvzc)）：

```c++
#include <fmt/format.h>

void vlog(const char* file, int line,
          fmt::string_view fmt, fmt::format_args args) {
  fmt::print("{}: {}: {}", file, line, fmt::vformat(fmt, args));
}

template <typename... T>
void log(const char* file, int line,
         fmt::format_string<T...> fmt, T&&... args) {
  vlog(file, line, fmt, fmt::make_format_args(args...));
}

#define MY_LOG(fmt, ...) log(__FILE__, __LINE__, fmt, __VA_ARGS__)

MY_LOG("invalid squishiness: {}", 42);
```

注意 `vlog` 不对参数类型参数化，与完全参数化的版本相比，
这可缩短编译时间并减小二进制代码体积。

::: make_format_args(T&...)

::: basic_format_args

::: format_args

::: basic_format_arg

### 命名参数

::: arg(const char*, const T&)

### 兼容性

::: basic_string_view

::: string_view

## 格式 API

`fmt/format.h` 定义完整的格式 API，提供额外的格式化函数与
区域设置支持。

<a id="format"></a>
::: format(format_string<T...>, T&&...)

::: vformat(string_view, format_args)

::: operator""_a()

### 工具

::: ptr(T)

::: underlying(Enum)

::: to_string(const T&)

::: group_digits(T)

::: detail::buffer

::: basic_memory_buffer

### 系统错误

{fmt} 不使用 `errno` 向用户传递错误信息，但它可能调用会设置
`errno` 的系统函数。用户不应假设库函数会保持
`errno` 的值不变。

::: system_error

::: format_system_error

### 自定义分配器

{fmt} 库支持自定义动态内存分配器。自定义分配器类可作为
模板实参传给 [`fmt::basic_memory_buffer`](#basic_memory_buffer)：

    using custom_memory_buffer = 
      fmt::basic_memory_buffer<char, fmt::inline_buffer_size, custom_allocator>;

也可以编写使用自定义分配器的格式化函数：

    using custom_string =
      std::basic_string<char, std::char_traits<char>, custom_allocator>;

    auto vformat(custom_allocator alloc, fmt::string_view fmt,
                 fmt::format_args args) -> custom_string {
      auto buf = custom_memory_buffer(alloc);
      fmt::vformat_to(std::back_inserter(buf), fmt, args);
      return custom_string(buf.data(), buf.size(), alloc);
    }

    template <typename ...Args>
    auto format(custom_allocator alloc, fmt::string_view fmt,
                const Args& ... args) -> custom_string {
      return vformat(alloc, fmt, fmt::make_format_args(args...));
    }

该分配器仅用于输出容器。对于内置类型与字符串类型，
格式化函数通常不做任何分配；例外是非默认的浮点格式化
偶尔会退回到 `sprintf`。

### 区域设置

默认情况下所有格式化均与区域设置无关。使用 `'L'` 格式说明符
可插入区域设置相应的数字分隔字符：

    #include <fmt/format.h>
    #include <locale>

    std::locale::global(std::locale("en_US.UTF-8"));
    auto s = fmt::format("{:L}", 1000000);  // s == "1,000,000"

`fmt/format.h` 提供以下接受 `std::locale` 参数的格式化函数重载。
区域设置类型是模板参数，以避免代价高昂的 `<locale>` 包含。

::: format(locale_ref, format_string<T...>, T&&...)

::: format_to(OutputIt, locale_ref, format_string<T...>, T&&...)

::: formatted_size(locale_ref, format_string<T...>, T&&...)

<a id="legacy-checks"></a>
### 旧式编译时检查

`FMT_STRING` 在较旧的编译器上启用编译时检查。它要求
C++14 或更高版本，在 C++11 中是空操作。

::: FMT_STRING

要强制使用旧式编译时检查，请定义预处理器变量
`FMT_ENFORCE_COMPILE_STRING`。设置后，接受 `FMT_STRING`
的函数在遇到普通字符串时将编译失败。

<a id="ranges-api"></a>
## 范围与元组格式化

`fmt/ranges.h` 为范围与元组提供格式化支持：

    #include <fmt/ranges.h>

    fmt::print("{}", std::tuple<char, int>{'a', 42});
    // Output: ('a', 42)

借助 `fmt::join`，可用自定义分隔符分隔元组元素：

    #include <fmt/ranges.h>

    auto t = std::tuple<int, char>{1, 'a'};
    fmt::print("{}", fmt::join(t, ", "));
    // Output: 1, a

::: join(Range&&, string_view)

::: join(It, Sentinel, string_view)

::: join(std::initializer_list<T>, string_view)

<a id="chrono-api"></a>
## 日期与时间格式化

`fmt/chrono.h` 为以下类型提供格式化器：

- [`std::chrono::duration`](https://en.cppreference.com/w/cpp/chrono/duration)
- [`std::chrono::time_point`](
  https://en.cppreference.com/w/cpp/chrono/time_point)
- [`std::tm`](https://en.cppreference.com/w/cpp/chrono/c/tm)

格式语法见[时间日期格式规范](syntax.md#
chrono-format-spec)。

**示例**：

    #include <fmt/chrono.h>

    int main() {
      auto now = std::chrono::system_clock::now();

      fmt::print("The date is {:%Y-%m-%d}.\n", now);
      // Output: The date is 2020-11-07.
      // (with 2020-11-07 replaced by the current date)

      using namespace std::literals::chrono_literals;

      fmt::print("Default format: {} {}\n", 42s, 100ms);
      // Output: Default format: 42s 100ms

      fmt::print("strftime-like format: {:%H:%M:%S}\n", 3h + 15min + 30s);
      // Output: strftime-like format: 03:15:30
    }

::: gmtime(std::time_t)

<a id="std-api"></a>
## 标准库类型格式化

`fmt/std.h` 为以下类型提供格式化器：

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

::: ptr(const std::unique_ptr<T, Deleter>&)

::: ptr(const std::shared_ptr<T>&)

### 变体

`std::variant` 仅在其每个备选类型都可格式化时才能被格式化，
且需要 `__cpp_lib_variant` [库特性](https://en.cppreference.com/w/cpp/feature_test)。

**示例**：

    #include <fmt/std.h>

    fmt::print("{}", std::variant<char, float>('x'));
    // Output: variant('x')

    fmt::print("{}", std::variant<std::monostate, char>());
    // Output: variant(monostate)

## 位域与紧凑结构体

要格式化位域，或应用了 `__attribute__((packed))` 的结构体字段，
需通过强制转换或一元 `+` 将其转换为底层或兼容类型
（[godbolt](https://www.godbolt.org/z/3qKKs6T5Y)）：

```c++
struct smol {
  int bit : 1;
};

auto s = smol();
fmt::print("{}", +s.bit);
```

这是 C++ 中"完美"转发的一个已知局限。

<a id="enum-api"></a>
## 枚举格式化

`fmt/enum.h` 提供对以 `fmt::as_identifiers` 注解的枚举的格式化。
此类枚举会格式化为与被格式化值匹配的枚举项的标识符：

    #include <fmt/enum.h>

    enum class [[=fmt::as_identifiers]] color { red, green, blue };

    fmt::print("{}", color::green);
    // Output: green

此类枚举使用字符串[格式规范](
syntax.md#format-specification)格式化，例如：

    fmt::print("[{:>7}]", color::red);
    // Output: [    red]

标识符仅以 `char` 字符串形式提供，因此注解枚举无法用
其他字符类型格式化。

若多个枚举项具有相同值，则按声明顺序取第一个。
未匹配任何枚举项的值会先以十进制底层值表示，
再应用字符串格式化：

    fmt::print("{}", static_cast<color>(42));
    // Output: 42

以 `fmt::as_underlying` 注解的枚举则使用整数[格式规范](
syntax.md#format-specification)格式化为底层值：

    enum class [[=fmt::as_underlying]] color { red = 1, green = 2, blue = 4 };

    fmt::print("{:04x}", color::blue);
    // Output: 0004

此类枚举在类型擦除前被映射到底层类型，因此还可用作
动态宽度或精度。与 `fmt::as_identifiers` 不同，
它适用于所有字符类型。两种注解指定不同的表示形式，
不能组合使用。

未注解的枚举不受影响，仍按原方式格式化——即限定作用域的
枚举需要 `format_as` 或 `formatter` 特化，见
[格式化用户定义类型](#udt)。

这利用了两个 C++26 特性：用于获取枚举项标识符的
[反射](https://en.cppreference.com/w/cpp/language/operator_reflection)，
以及用于通过 `fmt::as_identifiers` 将枚举纳入的
[注解](https://en.cppreference.com/w/cpp/language/annotations)。因此需要
支持反射的编译器，GCC 可能需要额外标志如 `-freflection`。宏
`FMT_USE_REFLECTION` 在反射可用时为 1，否则为 0。
用户也可自行定义它以禁用反射。

以模块方式构建 {fmt} 时，反射支持在模块自身编译时检测，
因此仅当模块构建时启用了反射，此 API 才对导入方可用。

<a id="compile-api"></a>
## 编译时支持

`fmt/compile.h` 提供格式字符串编译与编译时（`constexpr`）格式化，
通过 `FMT_COMPILE` 宏或命名空间 `fmt::literals` 中定义的 `_cf`
用户定义字面量启用。以 `FMT_COMPILE` 或 `_cf` 标记的格式字符串
会在编译时被解析、检查并转换为高效格式化代码。它支持内置与
字符串类型参数，也支持在 `formatter` 特化中 `format` 方法以
格式上下文类型为模板参数的用户定义类型。
例如（[在线运行](https://www.godbolt.org/z/3c13erEoq)）：

    struct point {
      double x;
      double y;
    };

    template <> struct fmt::formatter<point> {
      constexpr auto parse(format_parse_context& ctx) { return ctx.begin(); }

      template <typename FormatContext>
      auto format(const point& p, FormatContext& ctx) const {
        return format_to(ctx.out(), "({}, {})"_cf, p.x, p.y);
      }
    };

    using namespace fmt::literals;
    std::string s = fmt::format("{}"_cf, point(4, 2));

与默认 API 相比，格式字符串编译可能生成更多二进制代码，
因此仅建议在格式化为性能瓶颈之处使用。

同一组 API 还支持在编译时格式化，例如在 `constexpr`
与 `consteval` 函数中。此外还有实验性的
`FMT_STATIC_FORMAT`，可在编译时格式化为尺寸恰好所需的字符串。
编译时格式化适用于具有 `constexpr` `format` 方法的
内置与用户定义格式化器。示例：

    template <> struct fmt::formatter<point> {
      constexpr auto parse(format_parse_context& ctx) { return ctx.begin(); }

      template <typename FormatContext>
      constexpr auto format(const point& p, FormatContext& ctx) const {
        return format_to(ctx.out(), "({}, {})"_cf, p.x, p.y);
      }
    };

    constexpr auto s = FMT_STATIC_FORMAT("{}", point(4, 2));
    const char* cstr = s.c_str(); // Points the static string "(4, 2)".

::: operator""_cf

::: FMT_COMPILE

::: FMT_STATIC_FORMAT

<a id="color-api"></a>
## 终端颜色与文本样式

`fmt/color.h` 提供终端颜色与文本样式输出支持。

::: print(text_style, format_string<T...>, T&&...)

::: fg(detail::color_type)

::: bg(detail::color_type)

::: styled(const T&, text_style)

<a id="os-api"></a>
## 系统 API

::: ostream

::: output_file(cstring_view, T...)

::: windows_error

<a id="ostream-api"></a>
## `std::ostream` 支持

`fmt/ostream.h` 提供 `std::ostream` 支持，包括对重载了
插入运算符（`operator<<`）的用户定义类型的格式化。
要使类型可通过 `std::ostream` 格式化，请提供继承自
`ostream_formatter` 的 `formatter` 特化：

    #include <fmt/ostream.h>

    struct date {
      int year, month, day;

      friend std::ostream& operator<<(std::ostream& os, const date& d) {
        return os << d.year << '-' << d.month << '-' << d.day;
      }
    };

    template <> struct fmt::formatter<date> : ostream_formatter {};

    std::string s = fmt::format("The date is {}", date{2012, 12, 9});
    // s == "The date is 2012-12-9"

::: streamed(const T&)

::: print(std::ostream&, format_string<T...>, T&&...)

<a id="args-api"></a>
## 动态参数列表

头文件 `fmt/args.h` 提供 `dynamic_format_arg_store`——
一个构建器风格的 API，可用于动态构造格式参数列表。

::: dynamic_format_arg_store

<a id="printf-api"></a>
## 安全的 `printf`

头文件 `fmt/printf.h` 提供类 `printf` 的格式化功能。
以下函数使用 [printf 格式字符串语法](https://pubs.opengroup.org/onlinepubs/009695399/functions/fprintf.html)
（含位置参数的 POSIX 扩展）。与标准版本不同，
`fmt` 函数是类型安全的：若参数类型与其格式规范不匹配，
将抛出异常。

::: printf(string_view, const T&...)

::: fprintf(std::FILE*, string_view, const T&...)

::: sprintf(string_view, const T&...)

<a id="xchar-api"></a>
## 宽字符串

可选头文件 `fmt/xchar.h` 提供 `wchar_t` 与
其他特殊字符类型支持。

::: wstring_view

::: wformat_context

::: to_wstring(const T&)

## 与 C++20 `std::format` 的兼容性

{fmt} 实现了几乎全部 [C++20 格式化库](https://en.cppreference.com/w/cpp/utility/format) 功能，
但有以下差异：

- 名称定义在 `fmt` 命名空间而非 `std` 中，
  以避免与标准库实现冲突。

- 宽度计算不使用字素簇切分。后者已在单独分支实现，
  但尚未集成。

- {fmt} 的默认浮点表示使用能提供往返保证的最小精度，
  与 Java、Python 等语言类似。`std::format` 目前按
  `std::to_chars` 规定，后者尝试生成最少的字符
  （忽略冗余数字与指数中的符号），可能产生比必要更多的
  十进制数字。

## 配置选项

{fmt} 通过 CMake 选项与预处理器宏提供配置，
用于启用或禁用特性以及优化二进制体积。例如，配置 CMake 时
可用 `-DFMT_OS=OFF` 禁用 `fmt/os.h` 中定义的 OS 相关 API。

### CMake 选项

- **`FMT_OS`**：设为 `OFF` 时禁用 OS 相关 API（`fmt/os.h`）。
- **`FMT_UNICODE`**：设为 `OFF` 时在
  Windows/MSVC 上禁用 Unicode 支持。其他平台始终启用。

### 宏

- **`FMT_HEADER_ONLY`**：定义时启用仅头文件模式。
  是 `fmt::fmt-header-only` CMake 目标的替代方案。
  默认：未定义。

- **`FMT_USE_EXCEPTIONS`**：设为 `0` 时禁用异常。
  默认：`1`（以 `-fno-exceptions` 编译时为 `0`）。

- **`FMT_USE_LOCALE`**：设为 `0` 时禁用区域设置支持。
  默认：`1`（`FMT_OPTIMIZE_SIZE > 1` 时为 `0`）。

- **`FMT_CUSTOM_ASSERT_FAIL`**：设为 `1` 时允许用户提供
  自定义 `fmt::assert_fail` 函数，在断言失败时调用；
  若禁用异常，也在运行时错误时调用。默认：`0`。

- **`FMT_BUILTIN_TYPES`**：设为 `0` 时禁用对 `int` 之外的
  算术与字符串类型的内置处理。以每次调用开销为代价
  减小库体积。默认：`1`。

- **`FMT_OPTIMIZE_SIZE`**：控制二进制体积优化：
    - `0` —— 关闭（默认）
    - `1` —— 应用部分优化
    - `2` —— 默认禁用区域设置支持、部分 Unicode 特性与
      命名参数，并应用更激进的优化

### 二进制体积优化

要以牺牲部分特性为代价将 {fmt} 的二进制体积降到最低，
可使用以下配置：

- CMake 选项：
    - `FMT_OS=OFF`
- 宏：
    - `FMT_BUILTIN_TYPES=0`
    - `FMT_OPTIMIZE_SIZE=2`
