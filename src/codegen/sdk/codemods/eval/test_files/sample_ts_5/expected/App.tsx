import React from "react";
import { getUser } from "./userHelpers";

const Greeting: React.FC<{ name: string }> = ({ name }): JSX.Element => {
  return <h1>Hello, {name}!</h1>;
};

export const App: React.FC = (): JSX.Element => {
  const user = getUser();
  return (
    <div>
      <Greeting name={user.name} />
    </div>
  );
};
