---
hide:
  - navigation
  - toc
---

# 一个现代化的格式化库

<div class="features-container">

<div class="feature">
<h2>安全性</h2>
<p>
  受 Python 格式化设施的启发，{fmt} 为 <code>printf</code> 系列函数提供了
  安全的替代方案。格式字符串中的错误是 C 语言中常见的安全漏洞来源，
  而 {fmt} 能够<b>在编译时报告</b>这类错误。例如：

  <pre><code class="language-cpp"
  >fmt::format("{:d}", "I am not a number");</code></pre>

  由于 <code>d</code> 不是字符串的有效格式说明符，上述调用会产生编译时错误。
  诸如 <a href="api/#format">
  <code>fmt::format</code></a> 这样的 API 通过自动内存管理
  <b>防止缓冲区溢出错误</b>。
</p>
<a href="api#compile-time-checks">→ 了解更多</a>
</div>

<div class="feature">
<h2>可扩展性</h2>
<p>
  对大多数<b>标准类型</b>的格式化——包括所有容器、日期和时间——均
  <b>开箱即用</b>。例如：

  <pre><code class="language-cpp"
  >fmt::print("{}", std::vector{1, 2, 3});</code></pre>

  以类似 JSON 的格式打印该向量：

  <pre><code>[1, 2, 3]</code></pre>

  您可以<b>让自己的类型支持格式化</b>，甚至让编译时检查
  同样适用于它们。
</p>
<a href="api#udt">→ 了解更多</a>
</div>

<div class="feature">
<h2>性能</h2>
<p>
  与 iostreams 和 <code>sprintf</code> 相比，{fmt} 的速度可提升
  <b>数十个百分点至 20-30 倍</b>，数值格式化场景尤为明显。

<a href="https://github.com/fmtlib/fmt?tab=readme-ov-file#benchmarks">
<img src="perf.svg">
</a>

  该库<b>将动态内存分配降到最少</b>，还可选择
  <a href="api#compile-api">编译格式字符串</a>以生成最优代码。
</p>
</div>

<div class="feature">
<h2>Unicode 支持</h2>
<p>
  基于 UTF-8 与 <code>char</code> 字符串，{fmt} 在各主流操作系统上提供
  <b>可移植的 Unicode 支持</b>。例如：

  <pre><code class="language-cpp"
  >fmt::print("Слава Україні!");</code></pre>

  无论代码页如何设置，都能在 Linux、macOS 乃至
  Windows 控制台上正确打印。
</p>
<p>
  默认行为<b>与区域设置无关</b>，但您也可以选择启用本地化格式化，
  {fmt} 使其与 Unicode 协同工作，解决了标准库中的相关问题。
</p>
</div>

<div class="feature">
<h2>快速编译</h2>
<p>
  该库大量运用<b>类型擦除</b>来实现快速编译。
  <code>fmt/core.h</code> 提供了 API 的一个子集，
  <b>头文件包含依赖极少</b>，且功能足以替换所有
  <code>*printf</code> 的用法。
</p>
<p>
  使用 {fmt} 的代码通常比等价的 iostreams 代码编译快数倍；
  虽然 <code>printf</code> 的编译速度仍更快，但差距正在缩小。
</p>
<a href=
"https://github.com/fmtlib/fmt?tab=readme-ov-file#compile-time-and-code-bloat">
→ 了解更多</a>
</div>

<div class="feature">
<h2>二进制体积小</h2>
<p>
  类型擦除同样用于避免模板膨胀，从而生成<b>紧凑的
  单次调用二进制代码</b>。例如，带单个参数的 <code>fmt::print</code> 调用
  仅对应 <a href="https://godbolt.org/g/TZU4KF">几条指令</a>——尽管额外增加了
  运行时安全性，仍可与 <code>printf</code> 相媲美，且远小于
  等价的 iostreams 代码。
</p>
<p>
  库本身的二进制体积也很小，并且可以禁用部分组件
  （如浮点数格式化），使其在资源受限设备上更加精简。
</p>
</div>

<div class="feature">
<h2>可移植性</h2>
<p>
  {fmt} 拥有一个<b>小巧自包含的代码库</b>，核心仅由
  三个头文件组成，无任何外部依赖。
</p>
<p>
  该库具有高度可移植性，只需最基础的 <b>C++11 特性子集</b>——
  GCC 4.9、Clang 3.6、MSVC 19.10（2017）及更高版本均已支持。
  若有更新的编译器与标准库特性则会自动采用，并解锁更多功能。
</p>
<p>
  在可能的情况下，格式化函数的输出<b>跨平台保持一致</b>。
</p>
</div>

<div class="feature">
<h2>开源</h2>
<p>
  {fmt} 位列 GitHub 上百大开源 C++ 库，累计拥有
  <a href="https://github.com/fmtlib/fmt/graphs/contributors">数百位贡献者</a>。
</p>
<p>
  该库以宽松的 MIT
  <a href="https://github.com/fmtlib/fmt#license">许可证</a>发布，并
  <b>被众多开源项目所依赖</b>，包括 Blender、PyTorch、
  Apple 的 FoundationDB、Windows Terminal、MongoDB 等。
</p>
</div>

</div>
