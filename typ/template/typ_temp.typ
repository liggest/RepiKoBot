#import "../base/typ_base.typ": render-typ


#{
  let content_str = sys.inputs.at("content", default: "")
  let content_type = sys.inputs.at("content_type", default: "str")

  if content_type == "file" {
    content_str = read(content_str)
  }

  render-typ(content_str)
}

// #render-typ(````
// #rect[
//   ```python
//   def add(a, b):
//       return a + b # 中文怪怪的？
//   ```
//   $$
//     #sym.sum x = 3
//   $$

//   abc你好123

//   *abc你好123*

//   1. A1
//   2. B2
//   3. C3
//   10. D10
// ]
// ````.text)
