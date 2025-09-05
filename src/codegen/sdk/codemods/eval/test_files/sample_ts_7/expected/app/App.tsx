import React from "react";
import { getUser } from "./userHelpers";

/**
 * This function is intended for internal use within the module.
 * @param {string} input - The input string to process.
 * @returns {string} The processed output string.
 *
 * @internal
 */
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
