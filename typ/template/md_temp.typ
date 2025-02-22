#import "../base/md_base.typ": render-md, maybe-image

#{
  let content_str = sys.inputs.at("content", default: "")
  let content_type = sys.inputs.at("content_type", default: "str")

  if content_type == "file" {
    content_str = read(content_str)
  }

  render-md(content_str, scope: (image: (path, alt: none) => maybe-image(path, alt: alt)))
}

// #render-md(```
// # 今天真不错

// abc你好123

// **abc你好123**
// ```, scope: (image: (path, alt: none) => maybe-image(path, alt: alt)))
