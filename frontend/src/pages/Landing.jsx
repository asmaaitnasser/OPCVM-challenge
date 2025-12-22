import Navbar from "../components/Navbar";
import Hero from "../sections/Hero";
import Stats from "../sections/Stats";
import WhatIsOpcvm from "../sections/WhatIsOpcvm";
import OpcvmTypes from "../sections/OpcvmTypes";
import WhyFundWatch from "../sections/WhyFundWatch";
import Pipeline from "../sections/Pipeline";
import ForWho from "../sections/ForWho";
import Mission from "../sections/Mission";

export default function Landing() {
  return (
    <>
      <Navbar />
      <Hero />
      <Stats />
      <WhatIsOpcvm />
      <OpcvmTypes />
      <WhyFundWatch />
      <Pipeline />
      <ForWho />
      <Mission />
    </>
  );
}
