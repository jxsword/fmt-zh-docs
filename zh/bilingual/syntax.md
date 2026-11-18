# 双语对照：格式语法

> 本页为 `syntax.md` 的中英段落对照（DR-005 独立对照模式）。每段先中文译文，再以引用块给出英文原文；代码块为逐字保留内容，不参与对照。

## 格式字符串语法

> 原文标题：Format String Syntax

本库的格式化函数——最主要的是
[`fmt::format`](api.md#format) 与 [`fmt::print`](api.md#print)——接受
按本文所述语法编写的格式字符串。

```text
The formatting functions in this library — most notably
[`fmt::format`](api.md#format) and [`fmt::print`](api.md#print) — accept
format strings written in the syntax described here.
```

格式字符串是嵌入了*替换字段*的纯文本，替换字段由花括号 `{` 和 `}`
界定。替换字段之外的字符将原样复制到输出。若要输出字面花括号，请将其
双写：`{{` 会在输出中产生单个 `{`，`}}` 会产生单个 `}`。

```text
A format string is plain text with embedded *replacement fields* delimited by
the braces `{` and `}`. Characters outside of any replacement field are
copied to the output unchanged. To emit a literal brace, double it: `{{`
yields a single `{` in the output, and `}}` yields a single `}`.
```

替换字段由下述文法描述。

```text
A replacement field is described by the grammar below.
```

<a id="replacement-field"></a>
<pre><code class="language-json"
>replacement_field ::= "{" [arg_id] [":" (<a href="#format-spec"
  >format_spec</a> | <a href="#chrono-format-spec">chrono_format_spec</a>)] "}"
arg_id            ::= integer | identifier
integer           ::= digit+
digit             ::= "0"..."9"
identifier        ::= id_start id_continue*
id_start          ::= "a"..."z" | "A"..."Z" | "_"
id_continue       ::= id_start | digit</code>
</pre>

```text
<a id="replacement-field"></a>
<pre><code class="language-json"
>replacement_field ::= "{" [arg_id] [":" (<a href="#format-spec"
  >format_spec</a> | <a href="#chrono-format-spec">chrono_format_spec</a>)] "}"
arg_id            ::= integer | identifier
integer           ::= digit+
digit             ::= "0"..."9"
identifier        ::= id_start id_continue*
id_start          ::= "a"..."z" | "A"..."Z" | "_"
id_continue       ::= id_start | digit</code>
</pre>
```

*arg_id* 选择要格式化的参数。它可以是非负整数（位置引用），
也可以是与通过 [`fmt::arg`](api.md#arg) 传入的参数名相匹配的
标识符（命名引用）。省略 *arg_id* 时，参数按从左到右的顺序依次消耗；
这种*自动*索引必须在整条格式字符串中统一使用——混用自动索引与显式
数字索引将导致编译时错误（或在运行时抛出 `format_error`）。

```text
An *arg_id* selects which argument to format. It may be a non-negative
integer (positional reference) or an identifier matching the name of an
argument passed via [`fmt::arg`](api.md#arg) (named reference). When *arg_id*
is omitted, arguments are consumed in left-to-right order; this *automatic*
indexing must be used uniformly throughout the format string — mixing
automatic and explicit numeric ids is a compile-time error (or a
`format_error` at runtime).
```

*format_spec* 以 `:` 引入，描述值应如何呈现。其文法与类型相关；
标准内置类型所用形式见下一节。

```text
A *format_spec*, introduced by `:`, describes how the value should be
rendered. Its grammar is type-dependent; the form used by the standard
built-in types is documented in the next section.
```

例如：

```text
For example:
```

*format_spec* 中的 *width* 或 *precision* 本身也可写成嵌套替换字段——
`{}` 或 `{arg_id}`——此时其取值来自运行时的一个整数参数。
嵌套字段只接受 *arg_id*；其自身不能再包含 *format_spec*。

```text
A *width* or *precision* inside a *format_spec* may itself be written as a
nested replacement field — `{}` or `{arg_id}` — in which case it takes its
value from an integer argument at runtime. Nested fields accept only an
*arg_id*; they cannot themselves contain a *format_spec*.
```

## 格式规范

> 原文标题：Format Specification

下述文法描述了内置类型——整数、浮点值、字符、字符串、布尔值与
指针——所共享的 *format_spec*，同样适用于任何其 `formatter` 复用
fmt 解析器的用户定义类型。

```text
The grammar below describes the *format_spec* shared by the built-in
types — integers, floating-point values, characters, strings, booleans, and
pointers — as well as by any user-defined type whose `formatter` reuses
fmt's parser.
```

<a id="format-spec"></a>
<pre><code class="language-json"
>format_spec ::= [[fill]align][sign]["#"]["0"][width]["." precision]["L"][type]
fill        ::= &lt;a character other than '{' or '}'>
align       ::= "<" | ">" | "^"
sign        ::= "+" | "-" | " "
width       ::= <a href="#replacement-field">integer</a> | "{" [<a
  href="#replacement-field">arg_id</a>] "}"
precision   ::= <a href="#replacement-field">integer</a> | "{" [<a
  href="#replacement-field">arg_id</a>] "}"
type        ::= "a" | "A" | "b" | "B" | "c" | "d" | "e" | "E" | "f" | "F" |
                "g" | "G" | "o" | "p" | "s" | "x" | "X" | "?"</code>
</pre>

```text
<a id="format-spec"></a>
<pre><code class="language-json"
>format_spec ::= [[fill]align][sign]["#"]["0"][width]["." precision]["L"][type]
fill        ::= &lt;a character other than '{' or '}'>
align       ::= "<" | ">" | "^"
sign        ::= "+" | "-" | " "
width       ::= <a href="#replacement-field">integer</a> | "{" [<a
  href="#replacement-field">arg_id</a>] "}"
precision   ::= <a href="#replacement-field">integer</a> | "{" [<a
  href="#replacement-field">arg_id</a>] "}"
type        ::= "a" | "A" | "b" | "B" | "c" | "d" | "e" | "E" | "f" | "F" |
                "g" | "G" | "o" | "p" | "s" | "x" | "X" | "?"</code>
</pre>
```

某个选项是否有意义取决于被格式化的值；不适用于该值类型的选项
会在可能时于编译期诊断，否则抛出 `format_error`。

```text
Whether a particular option is meaningful depends on the value being
formatted; options that do not apply to a value's type are diagnosed at
compile time when possible and otherwise raise a `format_error`.
```

## 填充与对齐

> 原文标题：Fill and alignment

*align* 字段决定当 *width* 使字段宽于值的自然渲染宽度时，
填充应放置在何处。

```text
The *align* field selects where padding is placed when *width* makes the
field wider than the value's natural rendering.
```

| 选项 | 效果                                                            |
|--------|-------------------------------------------------------------------|
| `<`    | 左对齐；在右侧填充。非数值类型的默认值。      |
| `>`    | 右对齐；在左侧填充。数值类型的默认值。          |
| `^`    | 居中；若填充无法均分，多余的填充字符放在右侧。 |

```text
| Option | Effect                                                            |
|--------|-------------------------------------------------------------------|
| `<`    | Left-align; pad on the right. Default for non-numeric types.      |
| `>`    | Right-align; pad on the left. Default for numeric types.          |
| `^`    | Center the value; if the padding cannot be split evenly, the extra padding character goes on the right. |
```

*fill* 字符可以是 `{` 或 `}` 之外的任意单个 Unicode 码点，
编码方式与格式字符串一致。它取代默认的空格作为填充字符。
填充字符只有在其后紧跟 *align* 字符时才会被识别——否则将与其他
位置的选项无法区分——因此要使用自定义填充，必须同时指定对齐方式。

```text
The *fill* character is any single Unicode code point other than `{` or `}`,
encoded the same way as the format string. It supplies the padding character
in place of the default space. A fill character is recognized only when it is
immediately followed by an *align* character — otherwise it would be
indistinguishable from an option in another position — so to use a custom
fill you must also specify an alignment.
```

当值的自然渲染宽度已不小于 *width* 时，对齐不产生任何可观察的效果；
值绝不会被截断以适配宽度。

```text
Alignment has no observable effect when the value's natural rendering is
already at least as wide as *width*; the value is never truncated to fit.
```

## 符号

> 原文标题：Sign

*sign* 字段控制数值的符号如何输出。仅适用于有符号整数与
浮点类型。

```text
The *sign* field controls how the sign of a numeric value is emitted. It
applies to signed integer and floating-point types only.
```

| 选项 | 效果                                                            |
|--------|-------------------------------------------------------------------|
| `+`    | 总是输出符号（非负值输出 `+`，负值输出 `-`）。|
| `-`    | 仅对负值输出 `-`。这是默认行为。           |
| 空格 | 非负值输出前导空格，负值输出 `-`；用于对齐有符号数的列。 |

```text
| Option | Effect                                                            |
|--------|-------------------------------------------------------------------|
| `+`    | Always emit a sign (`+` for nonnegative values, `-` for negative).|
| `-`    | Emit `-` only for negative values. This is the default.           |
| space  | Emit a leading space for nonnegative values and `-` for negative ones; useful for aligning columns of signed numbers. |
```

浮点输出中会保留 `-0.0` 的符号。

```text
The sign of `-0.0` is preserved in floating-point output.
```

## 替代形式（`#`）

> 原文标题：Alternate form (`#`)

`#` 标志选择一种*替代形式*，其确切含义取决于呈现类型：

```text
The `#` flag selects an *alternate form* whose exact meaning depends on the
presentation type:
```

- 对以二进制、八进制或十六进制呈现的整数，它会在前面加上相应的前缀
  （`0b`/`0B`、`0` 或 `0x`/`0X`）。前缀的大小写跟随类型说明符——
  `x` 对应 `0x`，`X` 对应 `0X`，依此类推。
- 对浮点值，它强制小数点出现在输出中（即使按默认规则不会输出
  小数部分），并阻止 `g`/`G` 呈现类型移除尾数末尾的零。

```text
- For integers rendered in binary, octal, or hexadecimal, it prepends the
  appropriate base prefix (`0b`/`0B`, `0`, or `0x`/`0X`). The case of the
  prefix follows the case of the type specifier — `0x` for `x`, `0X` for
  `X`, and so on.
- For floating-point values, it forces the decimal point to appear in the
  output even if no fractional digits would otherwise be emitted, and
  prevents the `g`/`G` presentation types from removing trailing zeros from
  the significand.
```

非数值类型不接受 `#` 标志。

```text
The `#` flag is not accepted by non-numeric types.
```

## 零填充（`0`）

> 原文标题：Zero padding (`0`)

紧置于 *width* 之前的 `0` 会为数值类型启用感知符号的零填充。
零被插入到符号（或前缀，如有的话）与最高有效位之间，
使符号或 `0x` 前缀紧贴数字，而不是被空格隔开。
例如，对 `120` 应用 `{:+08d}` 会得到 `+0000120`。

```text
A `0` placed immediately before *width* enables sign-aware zero padding for
numeric types. Zeros are inserted between the sign (or base prefix, if any)
and the most significant digit, so that a sign or `0x` prefix stays adjacent
to the digits rather than being separated by spaces. For example, `{:+08d}`
applied to `120` produces `+0000120`.
```

零填充：

```text
Zero padding:
```

- 仅适用于数值类型；
- 对 `inf` 或 `nan` 无效；
- 同时显式指定 *align* 时将被忽略。

```text
- applies only to numeric types;
- has no effect on `inf` or `nan`;
- is ignored when an explicit *align* is also present.
```

## 宽度

> 原文标题：Width

*width* 是非负十进制整数，给出字段应占的最小字符数。
若格式化后的值短于 *width*，则按 *align* 与 *fill* 填充；
若长于 *width*，则完整写出。*width* 绝不会导致值被截断。

```text
*width* is a non-negative decimal integer giving the minimum number of
characters that the field should occupy. If the formatted value is shorter
than *width*, it is padded according to *align* and *fill*; if it is longer,
the value is written in full. *width* never causes the value to be
truncated.
```

要在运行时提供 *width*，可将该字段写作 `{}` 以消耗下一个参数，
或写作 `{arg_id}` 以按位置或名称引用一个整数参数。

```text
To supply *width* at runtime, write the field as `{}` to consume the next
argument, or as `{arg_id}` to reference an integer argument by position or
by name.
```

格式化字符串时，"宽度"以显示列数度量，采用感知 Unicode 的估算
（东亚宽字符与全角字符以及常见 emoji 区间计为两列，其余计为一列）。
这使得在等宽渲染下混排拉丁文与 CJK 文本时，
固定 *width* 在视觉上保持一致。

```text
When formatting strings, "width" is measured in display columns using a
Unicode-aware estimate (East Asian wide and fullwidth characters, plus
common emoji ranges, count as two columns; everything else counts as one).
This keeps fixed *width* values visually consistent in monospace renderings
that combine Latin and CJK text.
```

## 精度

> 原文标题：Precision

*precision* 是非负十进制整数（以 `.` 引入），其含义取决于
被格式化的值。与 *width* 一样，它也可作为嵌套替换字段
在运行时求值。

```text
*precision* is a non-negative decimal integer (introduced by `.`) whose
meaning depends on the value being formatted. As with *width*, it may be
supplied as a nested replacement field for runtime evaluation.
```

| 类型                          | `.precision` 的含义                       |
|-------------------------------|-----------------------------------------------|
| `e`, `E`, `f`, `F`            | 小数点后输出的位数。       |
| `g`, `G`                      | 有效数字的总位数。           |
| `a`, `A`                      | 十六进制尾数中小数点后的位数。若省略，则仅输出恰好能精确往返表示该值所需的位数。 |
| 字符串（`s`、`?` 或默认） | 从值中复制的码点数上限。 |

```text
| Type                          | Meaning of `.precision`                       |
|-------------------------------|-----------------------------------------------|
| `e`, `E`, `f`, `F`            | Digits emitted after the decimal point.       |
| `g`, `G`                      | Total number of significant digits.           |
| `a`, `A`                      | Digits after the decimal point in the hexadecimal significand. If omitted, just enough digits are emitted to round-trip the value exactly. |
| Strings (`s`, `?`, or default) | Upper bound on the number of code points copied from the value. |
```

整数、字符、布尔与指针类型不接受 *precision*。
当 *precision* 限制从 C 字符串取用的字符数时，
该字符串仍必须以空字符结尾。

```text
A *precision* is not accepted for integer, character, boolean, or pointer
types. When a *precision* limits the number of characters taken from a C
string, the string must still be null-terminated.
```

## 区域设置（`L`）

> 原文标题：Locale (`L`)

`L` 标志为数值类型选择随区域设置变化的格式化。
格式化器会检查传给格式化函数的 C++ 区域设置
（未传入时使用全局区域设置），并插入该区域设置的数字分组字符——
对浮点值还包括其小数点。该标志对非数值类型无效。

```text
The `L` flag selects locale-sensitive formatting for numeric types. The
formatter inspects the C++ locale supplied to the formatting function (or
the global locale, if none was passed) and inserts the locale's digit
grouping characters and — for floating-point values — its decimal point.
The flag has no effect on non-numeric types.
```

## 呈现类型

> 原文标题：Presentation type

*type* 字段选择值的表示形式。下面按适用的值类别对说明符分组。

```text
The *type* field chooses the representation for the value. Specifiers are
grouped below by the value categories they apply to.
```

**整数、布尔值与字符：**

```text
**Integers, booleans, and characters:**
```

| 类型 | 效果                                                              |
|------|---------------------------------------------------------------------|
| `b`  | 以 2 为基数。`#` 标志会添加 `0b` 前缀。                            |
| `B`  | 以 2 为基数。`#` 标志会添加 `0B` 前缀。                            |
| `c`  | 将整数渲染为该码点对应的字符。不适用于 `bool`。 |
| `d`  | 以 10 为基数。整数类型的默认值。                             |
| `o`  | 以 8 为基数。                                                             |
| `x`  | 以 16 为基数，小写数字。`#` 标志会添加 `0x` 前缀。        |
| `X`  | 以 16 为基数，大写数字。`#` 标志会添加 `0X` 前缀。        |
| none | 整数等同 `d`，字符等同 `c`，`bool` 为文本形式（`true`/`false`）。 |

```text
| Type | Effect                                                              |
|------|---------------------------------------------------------------------|
| `b`  | Base 2. The `#` flag adds a `0b` prefix.                            |
| `B`  | Base 2. The `#` flag adds a `0B` prefix.                            |
| `c`  | Render the integer as the character with that code point. Not allowed for `bool`. |
| `d`  | Base 10. The default for integer types.                             |
| `o`  | Base 8.                                                             |
| `x`  | Base 16, lower-case digits. The `#` flag adds a `0x` prefix.        |
| `X`  | Base 16, upper-case digits. The `#` flag adds a `0X` prefix.        |
| none | Same as `d` for integers, `c` for characters, and the textual form (`true`/`false`) for `bool`. |
```

**浮点值：**

```text
**Floating-point values:**
```

| 类型 | 效果                                                              |
|------|---------------------------------------------------------------------|
| `a`  | 十六进制尾数形式（如 `0x1.8p+1`）。数字与二进制指数的 `p` 均为小写。始终输出 `0x` 前缀，与 printf 的 `%a` 一致。`#` 标志强制输出小数点（如 `0x1.p+1`）。
| `A`  | 同 `a`，但全部使用大写。                             |
| `e`  | 科学计数法，十进制指数使用小写 `e`。 |
| `E`  | 科学计数法，使用大写 `E`。                         |
| `f`  | 定点表示。                                               |
| `F`  | 同 `f`，但将 `nan` 渲染为 `NAN`、`inf` 渲染为 `INF`。         |
| `g`  | 通用形式：当指数小于 &minus;4 或不小于精度时用科学计数法，否则用定点表示；除非设置了 `#`，否则会移除小数部分末尾的零。精度为 `0` 时按 `1` 解释。 |
| `G`  | 同 `g`，但指数使用 `E`，并输出大写 `INF`/`NAN`。 |
| none | 最短往返表示：格式化结果再解析回同一浮点类型时，逐位复现输入。 |

```text
| Type | Effect                                                              |
|------|---------------------------------------------------------------------|
| `a`  | Hexadecimal-significand form (e.g. `0x1.8p+1`). Lower-case digits and a lower-case `p` for the binary exponent. The `0x` prefix is always emitted, matching printf's `%a`. The `#` flag forces a decimal point (e.g. `0x1.p+1`).
| `A`  | Same as `a`, but upper-case throughout.                             |
| `e`  | Scientific notation with a lower-case `e` for the decimal exponent. |
| `E`  | Scientific notation with an upper-case `E`.                         |
| `f`  | Fixed-point notation.                                               |
| `F`  | Same as `f`, but renders `nan` as `NAN` and `inf` as `INF`.         |
| `g`  | General form: scientific notation when the exponent would be less than &minus;4 or not less than the precision, otherwise fixed-point; trailing zeros are removed from the fractional part unless `#` is set. A precision of `0` is interpreted as `1`. |
| `G`  | Same as `g`, but uses `E` for the exponent and upper-case `INF`/`NAN`. |
| none | Shortest round-trip representation: the formatted value, when parsed back into the same floating-point type, reproduces the input bit for bit. |
```

**字符串与字符：**

```text
**Strings and characters:**
```

| 类型 | 效果                                                              |
|------|---------------------------------------------------------------------|
| `s`  | 普通字符串输出。字符串类型与 `bool`（渲染为 `true` 或 `false`）的默认值。 |
| `c`  | 字符输出。字符类型的默认值。不适用于 `bool`。 |
| `?`  | 调试输出：值被包在单引号（字符）或双引号（字符串）中，不可打印、非 ASCII 及特殊字符以 C 风格转义序列转义，例如 `\n`、`\t`、`\"`、`\u{...}`。 |
| none | 字符串与 `bool` 等同 `s`，字符等同 `c`。      |

```text
| Type | Effect                                                              |
|------|---------------------------------------------------------------------|
| `s`  | Plain string output. Default for string types and for `bool` (which is rendered as `true` or `false`). |
| `c`  | Character output. Default for character types. Not allowed for `bool`. |
| `?`  | Debug output: the value is wrapped in single quotes (characters) or double quotes (strings), and non-printable, non-ASCII, and special characters are escaped using C-style escape sequences such as `\n`, `\t`, `\"`, and `\u{...}`. |
| none | Same as `s` for strings and `bool`, and as `c` for characters.      |
```

**指针：**

```text
**Pointers:**
```

| 类型 | 效果                                                              |
|------|---------------------------------------------------------------------|
| `p`  | 以 `0x` 为前缀的十六进制地址。指针类型的默认值。    |
| none | 等同 `p`。                                                        |

```text
| Type | Effect                                                              |
|------|---------------------------------------------------------------------|
| `p`  | Hexadecimal address prefixed by `0x`. Default for pointer types.    |
| none | Same as `p`.                                                        |
```

C 字符串（`char*` 或 `const char*`）同时接受字符串呈现类型
与 `p`，因此同一个值既可格式化为文本，也可格式化为地址。

```text
A C string (`char*` or `const char*`) accepts both the string presentation
types and `p`, so the same value can be formatted as either text or an
address.
```

## 时间日期格式规范

> 原文标题：Chrono Format Specification

时长与时间点类型以及 `std::tm` 的格式规范具有如下语法：

```text
The format specification for chrono duration and time point types as well
as `std::tm` has the following syntax:
```

<a id="chrono-format-spec"></a>
<pre><code class="language-json"
>chrono_format_spec ::= [[<a href="#format-spec">fill</a>]<a href="#format-spec"
  >align</a>][<a href="#format-spec">width</a>]["." <a href="#format-spec"
  >precision</a>][chrono_specs]
chrono_specs       ::= conversion_spec |
                       chrono_specs (conversion_spec | literal_char)
conversion_spec    ::= "%" [padding_modifier] [locale_modifier] chrono_type
literal_char       ::= &lt;a character other than '{', '}' or '%'>
padding_modifier   ::= "-" | "_"
locale_modifier    ::= "E" | "O"
chrono_type        ::= "a" | "A" | "b" | "B" | "c" | "C" | "d" | "D" | "e" |
                       "F" | "g" | "G" | "h" | "H" | "I" | "j" | "m" | "M" |
                       "n" | "p" | "q" | "Q" | "r" | "R" | "S" | "t" | "T" |
                       "u" | "U" | "V" | "w" | "W" | "x" | "X" | "y" | "Y" |
                       "z" | "Z" | "%"</code>
</pre>

```text
<a id="chrono-format-spec"></a>
<pre><code class="language-json"
>chrono_format_spec ::= [[<a href="#format-spec">fill</a>]<a href="#format-spec"
  >align</a>][<a href="#format-spec">width</a>]["." <a href="#format-spec"
  >precision</a>][chrono_specs]
chrono_specs       ::= conversion_spec |
                       chrono_specs (conversion_spec | literal_char)
conversion_spec    ::= "%" [padding_modifier] [locale_modifier] chrono_type
literal_char       ::= &lt;a character other than '{', '}' or '%'>
padding_modifier   ::= "-" | "_"
locale_modifier    ::= "E" | "O"
chrono_type        ::= "a" | "A" | "b" | "B" | "c" | "C" | "d" | "D" | "e" |
                       "F" | "g" | "G" | "h" | "H" | "I" | "j" | "m" | "M" |
                       "n" | "p" | "q" | "Q" | "r" | "R" | "S" | "t" | "T" |
                       "u" | "U" | "V" | "w" | "W" | "x" | "X" | "y" | "Y" |
                       "z" | "Z" | "%"</code>
</pre>
```

字面字符将原样复制到输出。精度仅对以浮点类型为表示类型的
`std::chrono::duration` 有效。

```text
Literal chars are copied unchanged to the output. Precision is valid only
for `std::chrono::duration` types with a floating-point representation type.
```

可用的呈现类型（*chrono_type*）如下：

```text
The available presentation types (*chrono_type*) are:
```

<table>
<tr>
  <th>类型</th>
  <th>含义</th>
</tr>
<tr>
  <td><code>'a'</code></td>
  <td>
    星期几的缩写名，例如 "Sat"。若值中不含有效的星期几，
    则抛出 <code>format_error</code> 类型异常。
  </td>
</tr>
<tr>
  <td><code>'A'</code></td>
  <td>
    星期几的全名，例如 "Saturday"。若值中不含有效的星期几，
    则抛出 <code>format_error</code> 类型异常。
  </td>
</tr>
<tr>
  <td><code>'b'</code></td>
  <td>
    月份的缩写名，例如 "Nov"。若值中不含有效的月份，
    则抛出 <code>format_error</code> 类型异常。
  </td>
</tr>
<tr>
  <td><code>'B'</code></td>
  <td>
    月份的全名，例如 "November"。若值中不含有效的月份，
    则抛出 <code>format_error</code> 类型异常。
  </td>
</tr>
<tr>
  <td><code>'c'</code></td>
  <td>
    日期与时间的表示，例如 "Sat Nov 12 22:04:00 1955"。修饰命令
    <code>%Ec</code> 产生区域设置的备用日期与时间表示。
  </td>
</tr>
<tr>
  <td><code>'C'</code></td>
  <td>
    以向下取整除法将年份除以 100 的结果，例如 "19"。若结果
    为单个十进制数字，则前面补 0。修饰命令
    <code>%EC</code> 产生区域设置对世纪的备用表示。
  </td>
</tr>
<tr>
  <td><code>'d'</code></td>
  <td>
    以十进制数表示的日。若结果为单个十进制数字，则前面补 0。修饰命令
    <code>%Od</code> 产生区域设置的备用表示。
  </td>
</tr>
<tr>
  <td><code>'D'</code></td>
  <td>等同 <code>%m/%d/%y</code>，例如 "11/12/55"。</td>
</tr>
<tr>
  <td><code>'e'</code></td>
  <td>
    以十进制数表示的日。若结果为单个十进制数字，则前面补一个空格。修饰命令
    <code>%Oe</code> 产生区域设置的备用表示。
  </td>
</tr>
<tr>
  <td><code>'F'</code></td>
  <td>等同 <code>%Y-%m-%d</code>，例如 "1955-11-12"。</td>
</tr>
<tr>
  <td><code>'g'</code></td>
  <td>
    基于 ISO 周的年份的最后两位十进制数字。若结果为
    单个数字，则前面补 0。
  </td>
</tr>
<tr>
  <td><code>'G'</code></td>
  <td>
    以十进制数表示的基于 ISO 周的年份。若结果不足
    四位，则左侧补 0 至四位。
  </td>
</tr>
<tr>
  <td><code>'h'</code></td>
  <td>等同 <code>%b</code>，例如 "Nov"。</td>
</tr>
<tr>
  <td><code>'H'</code></td>
  <td>
    以十进制数表示的小时（24 小时制）。若结果为单个数字，
    则前面补 0。修饰命令 <code>%OH</code>
    产生区域设置的备用表示。
  </td>
</tr>
<tr>
  <td><code>'I'</code></td>
  <td>
    以十进制数表示的小时（12 小时制）。若结果为单个数字，
    则前面补 0。修饰命令 <code>%OI</code>
    产生区域设置的备用表示。
  </td>
</tr>
<tr>
  <td><code>'j'</code></td>
  <td>
    若被格式化的类型是 duration 的特化，则为不补零的天数十进制数；
    否则为以十进制数表示的年中第几天。1 月 1 日为 001。
    若结果不足三位，则左侧补 0 至三位。
  </td>
</tr>
<tr>
  <td><code>'m'</code></td>
  <td>
    以十进制数表示的月份。1 月为 01。若结果为单个数字，
    则前面补 0。修饰命令 <code>%Om</code> 产生
    区域设置的备用表示。
  </td>
</tr>
<tr>
  <td><code>'M'</code></td>
  <td>
    以十进制数表示的分钟。若结果为单个数字，则
    前面补 0。修饰命令 <code>%OM</code> 产生
    区域设置的备用表示。
  </td>
</tr>
<tr>
  <td><code>'n'</code></td>
  <td>换行字符。</td>
</tr>
<tr>
  <td><code>'p'</code></td>
  <td>与 12 小时制关联的 AM/PM 标记。</td>
</tr>
<tr>
  <td><code>'q'</code></td>
  <td>时长的单位后缀。</td>
</tr>
<tr>
  <td><code>'Q'</code></td>
  <td>
    时长的数值（如同通过 <code>.count()</code> 提取）。
  </td>
</tr>
<tr>
  <td><code>'r'</code></td>
  <td>12 小时制时间，例如 "10:04:00 PM"。</td>
</tr>
<tr>
  <td><code>'R'</code></td>
  <td>等同 <code>%H:%M</code>，例如 "22:04"。</td>
</tr>
<tr>
  <td><code>'S'</code></td>
  <td>
    以十进制数表示的秒。若秒数小于 10，则结果前面补 0。
    若输入的精度无法用整数秒精确表示，则格式为固定格式的
    十进制浮点数，其精度与输入精度一致（若转换为浮点
    十进制秒无法在 18 位小数内完成，则取微秒精度）。修饰
    命令 <code>%OS</code> 产生区域设置的备用表示。
  </td>
</tr>
<tr>
  <td><code>'t'</code></td>
  <td>水平制表字符。</td>
</tr>
<tr>
  <td><code>'T'</code></td>
  <td>等同 <code>%H:%M:%S</code>。</td>
</tr>
<tr>
  <td><code>'u'</code></td>
  <td>
    以十进制数表示的 ISO 星期几（1-7），周一为 1。修饰
    命令 <code>%Ou</code> 产生区域设置的备用表示。
  </td>
</tr>
<tr>
  <td><code>'U'</code></td>
  <td>
    以十进制数表示的年中第几周。当年第一个周日是第 01 周的
    第一天；在此之前的日子属第 00 周。若结果为单个数字，
    则前面补 0。修饰命令 <code>%OU</code> 产生区域设置的
    备用表示。
  </td>
</tr>
<tr>
  <td><code>'V'</code></td>
  <td>
    以十进制数表示的基于 ISO 周的周数。若结果为
    单个数字，则前面补 0。修饰命令 <code>%OV</code>
    产生区域设置的备用表示。
  </td>
</tr>
<tr>
  <td><code>'w'</code></td>
  <td>
    以十进制数表示的星期几（0-6），周日为 0。修饰
    命令 <code>%Ow</code> 产生区域设置的备用表示。
  </td>
</tr>
<tr>
  <td><code>'W'</code></td>
  <td>
    以十进制数表示的年中第几周。当年第一个周一是第 01 周的
    第一天；在此之前的日子属第 00 周。若结果为单个数字，
    则前面补 0。修饰命令 <code>%OW</code> 产生区域设置的
    备用表示。
  </td>
</tr>
<tr>
  <td><code>'x'</code></td>
  <td>
    日期表示，例如 "11/12/55"。修饰命令
    <code>%Ex</code> 产生区域设置的备用日期表示。
  </td>
</tr>
<tr>
  <td><code>'X'</code></td>
  <td>
    时间表示，例如 "10:04:00"。修饰命令
    <code>%EX</code> 产生区域设置的备用时间表示。
  </td>
</tr>
<tr>
  <td><code>'y'</code></td>
  <td>
    年份的最后两位十进制数字。若结果为单个数字，
    则前面补 0。修饰命令 <code>%Oy</code> 产生
    区域设置的备用表示。修饰命令 <code>%Ey</code>
    产生区域设置相对 <code>%EC</code>（仅年份）偏移量的备用表示。
  </td>
</tr>
<tr>
  <td><code>'Y'</code></td>
  <td>
    以十进制数表示的年份。若结果不足四位，则
    左侧补 0 至四位。修饰命令 <code>%EY</code>
    产生区域设置的备用全年表示。
  </td>
</tr>
<tr>
  <td><code>'z'</code></td>
  <td>
    ISO 8601:2004 格式的 UTC 偏移。例如 -0430 表示
    比 UTC 慢 4 小时 30 分。若偏移为零，则使用 +0000。
    修饰命令 <code>%Ez</code> 与 <code>%Oz</code> 在
    小时与分钟之间插入 <code>:</code>：-04:30。若偏移
    信息不可用，则抛出 <code>format_error</code> 类型异常。
  </td>
</tr>
<tr>
  <td><code>'Z'</code></td>
  <td>
    时区缩写。若时区缩写不可用，
    则抛出 <code>format_error</code> 类型异常。
  </td>
</tr>
<tr>
  <td><code>'%'</code></td>
  <td>% 字符本身。</td>
</tr>
</table>

```text
<table>
<tr>
  <th>Type</th>
  <th>Meaning</th>
</tr>
<tr>
  <td><code>'a'</code></td>
  <td>
    The abbreviated weekday name, e.g. "Sat". If the value does not contain a
    valid weekday, an exception of type <code>format_error</code> is thrown.
  </td>
</tr>
<tr>
  <td><code>'A'</code></td>
  <td>
    The full weekday name, e.g. "Saturday". If the value does not contain a
    valid weekday, an exception of type <code>format_error</code> is thrown.
  </td>
</tr>
<tr>
  <td><code>'b'</code></td>
  <td>
    The abbreviated month name, e.g. "Nov". If the value does not contain a
    valid month, an exception of type <code>format_error</code> is thrown.
  </td>
</tr>
<tr>
  <td><code>'B'</code></td>
  <td>
    The full month name, e.g. "November". If the value does not contain a valid
    month, an exception of type <code>format_error</code> is thrown.
  </td>
</tr>
<tr>
  <td><code>'c'</code></td>
  <td>
    The date and time representation, e.g. "Sat Nov 12 22:04:00 1955". The
    modified command <code>%Ec</code> produces the locale's alternate date and
    time representation.
  </td>
</tr>
<tr>
  <td><code>'C'</code></td>
  <td>
    The year divided by 100 using floored division, e.g. "19". If the result
    is a single decimal digit, it is prefixed with 0. The modified command
    <code>%EC</code> produces the locale's alternative representation of the
    century.
  </td>
</tr>
<tr>
  <td><code>'d'</code></td>
  <td>
    The day of month as a decimal number. If the result is a single decimal
    digit, it is prefixed with 0. The modified command <code>%Od</code>
    produces the locale's alternative representation.
  </td>
</tr>
<tr>
  <td><code>'D'</code></td>
  <td>Equivalent to <code>%m/%d/%y</code>, e.g. "11/12/55".</td>
</tr>
<tr>
  <td><code>'e'</code></td>
  <td>
    The day of month as a decimal number. If the result is a single decimal
    digit, it is prefixed with a space. The modified command <code>%Oe</code>
    produces the locale's alternative representation.
  </td>
</tr>
<tr>
  <td><code>'F'</code></td>
  <td>Equivalent to <code>%Y-%m-%d</code>, e.g. "1955-11-12".</td>
</tr>
<tr>
  <td><code>'g'</code></td>
  <td>
    The last two decimal digits of the ISO week-based year. If the result is a
    single digit it is prefixed by 0.
  </td>
</tr>
<tr>
  <td><code>'G'</code></td>
  <td>
    The ISO week-based year as a decimal number. If the result is less than
    four digits it is left-padded with 0 to four digits.
  </td>
</tr>
<tr>
  <td><code>'h'</code></td>
  <td>Equivalent to <code>%b</code>, e.g. "Nov".</td>
</tr>
<tr>
  <td><code>'H'</code></td>
  <td>
    The hour (24-hour clock) as a decimal number. If the result is a single
    digit, it is prefixed with 0. The modified command <code>%OH</code>
    produces the locale's alternative representation.
  </td>
</tr>
<tr>
  <td><code>'I'</code></td>
  <td>
    The hour (12-hour clock) as a decimal number. If the result is a single
    digit, it is prefixed with 0. The modified command <code>%OI</code>
    produces the locale's alternative representation.
  </td>
</tr>
<tr>
  <td><code>'j'</code></td>
  <td>
    If the type being formatted is a specialization of duration, the decimal
    number of days without padding. Otherwise, the day of the year as a decimal
    number. Jan 1 is 001. If the result is less than three digits, it is
    left-padded with 0 to three digits.
  </td>
</tr>
<tr>
  <td><code>'m'</code></td>
  <td>
    The month as a decimal number. Jan is 01. If the result is a single digit,
    it is prefixed with 0. The modified command <code>%Om</code> produces the
    locale's alternative representation.
  </td>
</tr>
<tr>
  <td><code>'M'</code></td>
  <td>
    The minute as a decimal number. If the result is a single digit, it
    is prefixed with 0. The modified command <code>%OM</code> produces the
    locale's alternative representation.
  </td>
</tr>
<tr>
  <td><code>'n'</code></td>
  <td>A new-line character.</td>
</tr>
<tr>
  <td><code>'p'</code></td>
  <td>The AM/PM designations associated with a 12-hour clock.</td>
</tr>
<tr>
  <td><code>'q'</code></td>
  <td>The duration's unit suffix.</td>
</tr>
<tr>
  <td><code>'Q'</code></td>
  <td>
    The duration's numeric value (as if extracted via <code>.count()</code>).
  </td>
</tr>
<tr>
  <td><code>'r'</code></td>
  <td>The 12-hour clock time, e.g. "10:04:00 PM".</td>
</tr>
<tr>
  <td><code>'R'</code></td>
  <td>Equivalent to <code>%H:%M</code>, e.g. "22:04".</td>
</tr>
<tr>
  <td><code>'S'</code></td>
  <td>
    Seconds as a decimal number. If the number of seconds is less than 10, the
    result is prefixed with 0. If the precision of the input cannot be exactly
    represented with seconds, then the format is a decimal floating-point number
    with a fixed format and a precision matching that of the precision of the
    input (or to a microseconds precision if the conversion to floating-point
    decimal seconds cannot be made within 18 fractional digits). The modified
    command <code>%OS</code> produces the locale's alternative representation.
  </td>
</tr>
<tr>
  <td><code>'t'</code></td>
  <td>A horizontal-tab character.</td>
</tr>
<tr>
  <td><code>'T'</code></td>
  <td>Equivalent to <code>%H:%M:%S</code>.</td>
</tr>
<tr>
  <td><code>'u'</code></td>
  <td>
    The ISO weekday as a decimal number (1-7), where Monday is 1. The modified
    command <code>%Ou</code> produces the locale's alternative representation.
  </td>
</tr>
<tr>
  <td><code>'U'</code></td>
  <td>
    The week number of the year as a decimal number. The first Sunday of the
    year is the first day of week 01. Days of the same year prior to that are
    in week 00. If the result is a single digit, it is prefixed with 0.
    The modified command <code>%OU</code> produces the locale's alternative
    representation.
  </td>
</tr>
<tr>
  <td><code>'V'</code></td>
  <td>
    The ISO week-based week number as a decimal number. If the result is a
    single digit, it is prefixed with 0. The modified command <code>%OV</code>
    produces the locale's alternative representation.
  </td>
</tr>
<tr>
  <td><code>'w'</code></td>
  <td>
    The weekday as a decimal number (0-6), where Sunday is 0. The modified
    command <code>%Ow</code> produces the locale's alternative representation.
  </td>
</tr>
<tr>
  <td><code>'W'</code></td>
  <td>
    The week number of the year as a decimal number. The first Monday of the
    year is the first day of week 01. Days of the same year prior to that are
    in week 00. If the result is a single digit, it is prefixed with 0.
    The modified command <code>%OW</code> produces the locale's alternative
    representation.
  </td>
</tr>
<tr>
  <td><code>'x'</code></td>
  <td>
    The date representation, e.g. "11/12/55". The modified command
    <code>%Ex</code> produces the locale's alternate date representation.
  </td>
</tr>
<tr>
  <td><code>'X'</code></td>
  <td>
    The time representation, e.g. "10:04:00". The modified command
    <code>%EX</code> produces the locale's alternate time representation.
  </td>
</tr>
<tr>
  <td><code>'y'</code></td>
  <td>
    The last two decimal digits of the year. If the result is a single digit
    it is prefixed by 0. The modified command <code>%Oy</code> produces the
    locale's alternative representation. The modified command <code>%Ey</code>
    produces the locale's alternative representation of offset from
    <code>%EC</code> (year only).
  </td>
</tr>
<tr>
  <td><code>'Y'</code></td>
  <td>
    The year as a decimal number. If the result is less than four digits it is
    left-padded with 0 to four digits. The modified command <code>%EY</code>
    produces the locale's alternative full year representation.
  </td>
</tr>
<tr>
  <td><code>'z'</code></td>
  <td>
    The offset from UTC in the ISO 8601:2004 format. For example -0430 refers
    to 4 hours 30 minutes behind UTC. If the offset is zero, +0000 is used.
    The modified commands <code>%Ez</code> and <code>%Oz</code> insert a
    <code>:</code> between the hours and minutes: -04:30. If the offset
    information is not available, an exception of type
    <code>format_error</code> is thrown.
  </td>
</tr>
<tr>
  <td><code>'Z'</code></td>
  <td>
    The time zone abbreviation. If the time zone abbreviation is not available,
    an exception of type <code>format_error</code> is thrown.
  </td>
</tr>
<tr>
  <td><code>'%'</code></td>
  <td>A % character.</td>
</tr>
</table>
```

含日历成分的说明符（如 `'d'`，即日）仅对 `std::tm` 与时间点有效，
对时长无效。

```text
Specifiers that have a calendaric component such as `'d'` (the day of month)
are valid only for `std::tm` and time points but not durations.
```

可用的填充修饰符（*padding_modifier*）如下：

```text
The available padding modifiers (*padding_modifier*) are:
```

| 类型  | 含义                                 |
|-------|-----------------------------------------|
| `'_'` | 用空格填充数值结果。       |
| `'-'` | 不填充数值结果字符串。     |

```text
| Type  | Meaning                                 |
|-------|-----------------------------------------|
| `'_'` | Pad a numeric result with spaces.       |
| `'-'` | Do not pad a numeric result string.     |
```

这些修饰符仅支持 `'H'`、`'I'`、`'M'`、`'S'`、`'U'`、
`'V'`、`'W'`、`'Y'`、`'d'`、`'j'` 和 `'m'` 呈现类型。

```text
These modifiers are only supported for the `'H'`, `'I'`, `'M'`, `'S'`, `'U'`,
`'V'`, `'W'`, `'Y'`, `'d'`, `'j'` and `'m'` presentation types.
```

示例：

```text
Example:
```

## 范围格式规范

> 原文标题：Range Format Specification

范围类型的格式规范具有如下语法：

```text
The format specification for range types has the following syntax:
```

<pre><code class="language-json"
>range_format_spec ::= [[fill]align][width]["n"][range_type][":" range_underlying_spec]</code>
</pre>

```text
<pre><code class="language-json"
>range_format_spec ::= [[fill]align][width]["n"][range_type][":" range_underlying_spec]</code>
</pre>
```

`fill`、`align` 与 `width` 选项的含义与
[标准格式规范](#format-specification-mini-language)相同，
但 `:` 不能用作填充字符，因为它用于引入底层元素规范。
它们作用于整个格式化范围而非其元素。

```text
The `fill`, `align` and `width` options have the same meaning as in the
[standard format specification](#format-specification-mini-language), except
that `:` cannot be used as a fill character because it introduces the
underlying element specification. They apply to the whole formatted range
rather than to its elements.
```

`'n'` 选项格式化范围时省略开头与结尾的方括号。

```text
The `'n'` option formats the range without the opening and closing brackets.
```

`range_type` 可用的呈现类型如下：

```text
The available presentation types for `range_type` are:
```

| 类型   | 含义                                                    |
|--------|------------------------------------------------------------|
| none   | 默认格式。                                            |
| `'s'`  | 字符串格式。范围被格式化为字符串。         |
| `'?⁠s'` | 调试格式。范围被格式化为转义字符串。 |

```text
| Type   | Meaning                                                    |
|--------|------------------------------------------------------------|
| none   | Default format.                                            |
| `'s'`  | String format. The range is formatted as a string.         |
| `'?⁠s'` | Debug format. The range is formatted as an escaped string. |
```

若 `range_type` 为 `'s'` 或 `'?s'`，则范围的元素类型必须是字符类型。
`'n'` 选项与 `range_underlying_spec` 不能与
`'s'` 和 `'?s'` 同时使用。

```text
If `range_type` is `'s'` or `'?s'`, the range element type must be a character
type. The `'n'` option and `range_underlying_spec` are mutually exclusive with
`'s'` and `'?s'`.
```

`range_underlying_spec` 依据范围元素类型的 formatter 进行解析。

```text
The `range_underlying_spec` is parsed based on the formatter of the range's
element type.
```

默认情况下，字符或字符串范围会以转义并加引号的形式打印。
但只要提供了 `range_underlying_spec`（即使为空），字符或字符串
就会按所提供的规范打印。

```text
By default, a range of characters or strings is printed escaped and quoted.
But if any `range_underlying_spec` is provided (even if it is empty), then the
characters or strings are printed according to the provided specification.
```

示例：

```text
Examples:
```

## 组合示例

> 原文标题：A Combined Example

下面的示例将前文介绍的几个要素——嵌套替换字段、填充字符与
居中——结合起来，为一条消息绘制固定宽度的边框：

```text
The example below ties together several elements introduced above — nested
replacement fields, fill characters, and centering — to draw a fixed-width
box around a message:
```

输出：

```text
Output:
```

---
*对照段落数：76（代码块未计入）*
