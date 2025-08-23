#import "../base/md_base.typ": render-md, maybe-image

#{
  let content_str = sys.inputs.at("content", default: "")
  let content_type = sys.inputs.at("content_type", default: "str")

  if content_type == "file" {
    content_str = read(content_str)
  }

  render-md(content_str, image: (path, alt: none) => maybe-image(path, alt: alt))
}

// #render-md(```
// # 今天真不错

// abc你好123

// **abc你好123**

// 🎵😶💃🏻

// > 123  
// > ABC  
// > 甲乙丙  

// <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
//   <!-- 头部 -->
//   <circle cx="50" cy="20" r="10" stroke="black" fill="none" stroke-width="2"/>
//   <!-- 身体 -->
//   <line x1="50" y1="30" x2="50" y2="60" stroke="black" stroke-width="2"/>
//   <!-- 左臂 -->
//   <line x1="50" y1="45" x2="30" y2="45" stroke="black" stroke-width="2"/> 
//   <!-- 大臂 -->
//   <line x1="30" y1="45" x2="30" y2="25" stroke="black" stroke-width="2"/> 
//   <!-- 小臂 -->
//   <!-- 右臂 -->
//   <line x1="50" y1="45" x2="70" y2="45" stroke="black" stroke-width="2"/> 
//   <!-- 大臂 -->
//   <line x1="70" y1="45" x2="70" y2="65" stroke="black" stroke-width="2"/> 
//   <!-- 小臂 -->
//   <!-- 腿部保持原样 -->
//   <line x1="50" y1="60" x2="40" y2="80" stroke="black" stroke-width="2"/>
//   <line x1="50" y1="60" x2="60" y2="80" stroke="black" stroke-width="2"/>
// </svg>
// ```, image: (path, alt: none) => maybe-image(path, alt: alt))
