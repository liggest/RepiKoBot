#import "../base/help_base.typ": init, render-help

#show: init

#{
  let content_dict = sys.inputs.at("content", default: "../../help/typst/general.toml")
  // let content_dict = sys.inputs.at("content", default: bytes(""))

  content_dict = toml(content_dict)
  
  render-help(content_dict)
}
