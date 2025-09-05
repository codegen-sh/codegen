import React from "react";
import { getUser } from "./userHelpers";

const Greeting = ({ name }) => {
  return <h1>Hello, {name}!</h1>;
};

export const App = () => {
  const user = getUser();
  return (
    <div>
      <Greeting name={user.name} />
    </div>
  );
};
