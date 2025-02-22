#import "../base/tex_base.typ": render-tex

#{
  let content_str = sys.inputs.at("content", default: "")
  let content_type = sys.inputs.at("content_type", default: "str")

  if content_type == "file" {
    content_str = read(content_str)
  }

  render-tex(content_str)
}

// #render-tex(```
// \underbrace{\widehat{\overline{\left|\    \    _\cup\bigcap^\cup\    \cup^{\   }\bigcap_\cup\right|}}}
// ```)
