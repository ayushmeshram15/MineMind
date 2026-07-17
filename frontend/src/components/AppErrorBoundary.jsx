import React from "react";

export default class AppErrorBoundary extends React.Component {
  constructor(props){super(props);this.state={error:null};}
  static getDerivedStateFromError(error){return {error};}
  componentDidCatch(error, info){console.error("MineMind UI error", error, info);}
  render(){
    if(!this.state.error) return this.props.children;
    return <div className="module-error-boundary"><p className="eyebrow">MODULE RECOVERY</p><h2>This module could not render</h2><p>{this.state.error?.message || "Unexpected interface error"}</p><button onClick={()=>{this.setState({error:null});window.location.reload();}}>Reload MineMind</button></div>;
  }
}
