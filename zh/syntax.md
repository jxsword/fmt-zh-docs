# 格式字符串语法

本库的格式化函数——最主要的是
[`fmt::format`](api.md#format) 与 [`fmt::print`](api.md#print)——接受
按本文所述语法编写的格式字符串。

格式字符串是嵌入了*替换字段*的纯文本，替换字段由花括号 `{` 和 `}`
界定。替换字段之外的字符将原样复制到输出。若要输出字面花括号，请将其
双写：`{{` 会在输出中产生单个 `{`，`}}` 会产生单个 `}`。

替换字段由下述文法描述。

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

*arg_id* 选择要格式化的参数。它可以是非负整数（位置引用），
也可以是与通过 [`fmt::arg`](api.md#arg) 传入的参数名相匹配的
标识符（命名引用）。省略 *arg_id* 时，参数按从左到右的顺序依次消耗；
这种*自动*索引必须在整条格式字符串中统一使用——混用自动索引与显式
数字索引将导致编译时错误（或在运行时抛出 `format_error`）。

*format_spec* 以 `:` 引入，描述值应如何呈现。其文法与类型相关；
标准内置类型所用形式见下一节。

例如：

```c++
fmt::format("hello, {}", "world");
// Result: "hello, world"

fmt::format("{1}, {0}!", "world", "hello");
// Result: "hello, world!"

fmt::format("{greeting}, {name}!",
            fmt::arg("greeting", "hi"), fmt::arg("name", "fmt"));
// Result: "hi, fmt!"
```

*format_spec* 中的 *width* 或 *precision* 本身也可写成嵌套替换字段——
`{}` 或 `{arg_id}`——此时其取值来自运行时的一个整数参数。
嵌套字段只接受 *arg_id*；其自身不能再包含 *format_spec*。

## 格式规范

下述文法描述了内置类型——整数、浮点值、字符、字符串、布尔值与
指针——所共享的 *format_spec*，同样适用于任何其 `formatter` 复用
fmt 解析器的用户定义类型。

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

某个选项是否有意义取决于被格式化的值；不适用于该值类型的选项
会在可能时于编译期诊断，否则抛出 `format_error`。

### 填充与对齐

*align* 字段决定当 *width* 使字段宽于值的自然渲染宽度时，
填充应放置在何处。

| 选项 | 效果                                                            |
|--------|-------------------------------------------------------------------|
| `<`    | 左对齐；在右侧填充。非数值类型的默认值。      |
| `>`    | 右对齐；在左侧填充。数值类型的默认值。          |
| `^`    | 居中；若填充无法均分，多余的填充字符放在右侧。 |

*fill* 字符可以是 `{` 或 `}` 之外的任意单个 Unicode 码点，
编码方式与格式字符串一致。它取代默认的空格作为填充字符。
填充字符只有在其后紧跟 *align* 字符时才会被识别——否则将与其他
位置的选项无法区分——因此要使用自定义填充，必须同时指定对齐方式。

当值的自然渲染宽度已不小于 *width* 时，对齐不产生任何可观察的效果；
值绝不会被截断以适配宽度。

```c++
fmt::format("[{:<10}]", "42");   // Result: "[42        ]"
fmt::format("[{:>10}]", "42");   // Result: "[        42]"
fmt::format("[{:^10}]", "42");   // Result: "[    42    ]"
fmt::format("[{:*^10}]", "42");  // Result: "[****42****]"  - '*' as fill
```

### 符号

*sign* 字段控制数值的符号如何输出。仅适用于有符号整数与
浮点类型。

| 选项 | 效果                                                            |
|--------|-------------------------------------------------------------------|
| `+`    | 总是输出符号（非负值输出 `+`，负值输出 `-`）。|
| `-`    | 仅对负值输出 `-`。这是默认行为。           |
| 空格 | 非负值输出前导空格，负值输出 `-`；用于对齐有符号数的列。 |

浮点输出中会保留 `-0.0` 的符号。

```c++
fmt::format("{:+d} {:+d}", 7, -7);  // Result: "+7 -7"
fmt::format("{: d} {: d}", 7, -7);  // Result: " 7 -7"
```

### 替代形式（`#`）

`#` 标志选择一种*替代形式*，其确切含义取决于呈现类型：

- 对以二进制、八进制或十六进制呈现的整数，它会在前面加上相应的前缀
  （`0b`/`0B`、`0` 或 `0x`/`0X`）。前缀的大小写跟随类型说明符——
  `x` 对应 `0x`，`X` 对应 `0X`，依此类推。
- 对浮点值，它强制小数点出现在输出中（即使按默认规则不会输出
  小数部分），并阻止 `g`/`G` 呈现类型移除尾数末尾的零。

非数值类型不接受 `#` 标志。

### 零填充（`0`）

紧置于 *width* 之前的 `0` 会为数值类型启用感知符号的零填充。
零被插入到符号（或前缀，如有的话）与最高有效位之间，
使符号或 `0x` 前缀紧贴数字，而不是被空格隔开。
例如，对 `120` 应用 `{:+08d}` 会得到 `+0000120`。

零填充：

- 仅适用于数值类型；
- 对 `inf` 或 `nan` 无效；
- 同时显式指定 *align* 时将被忽略。

### 宽度

*width* 是非负十进制整数，给出字段应占的最小字符数。
若格式化后的值短于 *width*，则按 *align* 与 *fill* 填充；
若长于 *width*，则完整写出。*width* 绝不会导致值被截断。

要在运行时提供 *width*，可将该字段写作 `{}` 以消耗下一个参数，
或写作 `{arg_id}` 以按位置或名称引用一个整数参数。

格式化字符串时，"宽度"以显示列数度量，采用感知 Unicode 的估算
（东亚宽字符与全角字符以及常见 emoji 区间计为两列，其余计为一列）。
这使得在等宽渲染下混排拉丁文与 CJK 文本时，
固定 *width* 在视觉上保持一致。

```c++
fmt::format("[{:6}]", 42);
// Result: "[    42]"  - right-aligned by default
fmt::format("[{:6}]", "hi");
// Result: "[hi    ]"  - left-aligned by default
fmt::format("[{:{}}]", 42, 6);
// Result: "[    42]"  - width from an argument
```

### 精度

*precision* 是非负十进制整数（以 `.` 引入），其含义取决于
被格式化的值。与 *width* 一样，它也可作为嵌套替换字段
在运行时求值。

| 类型                          | `.precision` 的含义                       |
|-------------------------------|-----------------------------------------------|
| `e`, `E`, `f`, `F`            | 小数点后输出的位数。       |
| `g`, `G`                      | 有效数字的总位数。           |
| `a`, `A`                      | 十六进制尾数中小数点后的位数。若省略，则仅输出恰好能精确往返表示该值所需的位数。 |
| 字符串（`s`、`?` 或默认） | 从值中复制的码点数上限。 |

整数、字符、布尔与指针类型不接受 *precision*。
当 *precision* 限制从 C 字符串取用的字符数时，
该字符串仍必须以空字符结尾。

```c++
fmt::format("{:.2f}", 3.14159);        // Result: "3.14"
fmt::format("{:.3g}", 3.14159);        // Result: "3.14"
fmt::format("{:.4}", "hello, world");  // Result: "hell"
fmt::format("{:.{}f}", 3.14159, 4);
// Result: "3.1416"  - precision from an argument
```

### 区域设置（`L`）

`L` 标志为数值类型选择随区域设置变化的格式化。
格式化器会检查传给格式化函数的 C++ 区域设置
（未传入时使用全局区域设置），并插入该区域设置的数字分组字符——
对浮点值还包括其小数点。该标志对非数值类型无效。

```c++
auto loc = std::locale("en_US.UTF-8");
fmt::format(loc, "{:L}", 1234567890);     // Result: "1,234,567,890"
fmt::format(loc, "{:.2Lf}", 1234567.89);  // Result: "1,234,567.89"
```

### 呈现类型

*type* 字段选择值的表示形式。下面按适用的值类别对说明符分组。

**整数、布尔值与字符：**

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

```c++
fmt::format("{:d} {:#x} {:#o} {:#b}", 42, 42, 42, 42);
// Result: "42 0x2a 052 0b101010"

fmt::format("{:#06x}", 0xfe);  // # adds the prefix, 06 zero-pads to width 6
// Result: "0x00fe"
```

**浮点值：**

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

**字符串与字符：**

| 类型 | 效果                                                              |
|------|---------------------------------------------------------------------|
| `s`  | 普通字符串输出。字符串类型与 `bool`（渲染为 `true` 或 `false`）的默认值。 |
| `c`  | 字符输出。字符类型的默认值。不适用于 `bool`。 |
| `?`  | 调试输出：值被包在单引号（字符）或双引号（字符串）中，不可打印、非 ASCII 及特殊字符以 C 风格转义序列转义，例如 `\n`、`\t`、`\"`、`\u{...}`。 |
| none | 字符串与 `bool` 等同 `s`，字符等同 `c`。      |

```c++
fmt::format("{}",   "tab\there");  // Result contains a literal tab character.
fmt::format("{:?}", "tab\there");  // Result: "\"tab\\there\""
```

**指针：**

| 类型 | 效果                                                              |
|------|---------------------------------------------------------------------|
| `p`  | 以 `0x` 为前缀的十六进制地址。指针类型的默认值。    |
| none | 等同 `p`。                                                        |

C 字符串（`char*` 或 `const char*`）同时接受字符串呈现类型
与 `p`，因此同一个值既可格式化为文本，也可格式化为地址。

## 时间日期格式规范

时长与时间点类型以及 `std::tm` 的格式规范具有如下语法：

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

字面字符将原样复制到输出。精度仅对以浮点类型为表示类型的
`std::chrono::duration` 有效。

可用的呈现类型（*chrono_type*）如下：

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

含日历成分的说明符（如 `'d'`，即日）仅对 `std::tm` 与时间点有效，
对时长无效。

可用的填充修饰符（*padding_modifier*）如下：

| 类型  | 含义                                 |
|-------|-----------------------------------------|
| `'_'` | 用空格填充数值结果。       |
| `'-'` | 不填充数值结果字符串。     |

这些修饰符仅支持 `'H'`、`'I'`、`'M'`、`'S'`、`'U'`、
`'V'`、`'W'`、`'Y'`、`'d'`、`'j'` 和 `'m'` 呈现类型。

示例：

```c++
#include <fmt/chrono.h>

auto t = std::tm();
t.tm_year = 2010 - 1900;
t.tm_mon = 7;
t.tm_mday = 4;
t.tm_hour = 12;
t.tm_min = 15;
t.tm_sec = 58;
fmt::print("{:%Y-%m-%d %H:%M:%S}", t);
// Prints: 2010-08-04 12:15:58
```

## 范围格式规范

范围类型的格式规范具有如下语法：

<pre><code class="language-json"
>range_format_spec ::= [[fill]align][width]["n"][range_type][":" range_underlying_spec]</code>
</pre>

`fill`、`align` 与 `width` 选项的含义与
[标准格式规范](#format-specification-mini-language)相同，
但 `:` 不能用作填充字符，因为它用于引入底层元素规范。
它们作用于整个格式化范围而非其元素。

`'n'` 选项格式化范围时省略开头与结尾的方括号。

`range_type` 可用的呈现类型如下：

| 类型   | 含义                                                    |
|--------|------------------------------------------------------------|
| none   | 默认格式。                                            |
| `'s'`  | 字符串格式。范围被格式化为字符串。         |
| `'?⁠s'` | 调试格式。范围被格式化为转义字符串。 |

若 `range_type` 为 `'s'` 或 `'?s'`，则范围的元素类型必须是字符类型。
`'n'` 选项与 `range_underlying_spec` 不能与
`'s'` 和 `'?s'` 同时使用。

`range_underlying_spec` 依据范围元素类型的 formatter 进行解析。

默认情况下，字符或字符串范围会以转义并加引号的形式打印。
但只要提供了 `range_underlying_spec`（即使为空），字符或字符串
就会按所提供的规范打印。

示例：

```c++
fmt::print("{}", std::vector{10, 20, 30});
// Output: [10, 20, 30]
fmt::print("{::#x}", std::vector{10, 20, 30});
// Output: [0xa, 0x14, 0x1e]
fmt::print("{}", std::vector{'h', 'e', 'l', 'l', 'o'});
// Output: ['h', 'e', 'l', 'l', 'o']
fmt::print("{:n}", std::vector{'h', 'e', 'l', 'l', 'o'});
// Output: 'h', 'e', 'l', 'l', 'o'
fmt::print("{:s}", std::vector{'h', 'e', 'l', 'l', 'o'});
// Output: hello
fmt::print("{:?s}", std::vector{'h', 'e', 'l', 'l', 'o', '\n'});
// Output: "hello\n"
fmt::print("{::}", std::vector{'h', 'e', 'l', 'l', 'o'});
// Output: [h, e, l, l, o]
fmt::print("{::d}", std::vector{'h', 'e', 'l', 'l', 'o'});
// Output: [104, 101, 108, 108, 111]
fmt::print("{:n:f}", std::array{std::numbers::pi, std::numbers::e});
// Output: 3.141593, 2.718282
```

## 组合示例

下面的示例将前文介绍的几个要素——嵌套替换字段、填充字符与
居中——结合起来，为一条消息绘制固定宽度的边框：

```c++
fmt::print(
    "┌{0:─^{2}}┐\n"
    "│{1: ^{2}}│\n"
    "└{0:─^{2}}┘\n", "", "Hello, world!", 20);
```

输出：

```
┌────────────────────┐
│   Hello, world!    │
└────────────────────┘
```
