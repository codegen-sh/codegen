import { App } from "../app/App";
import { getUser } from "../app/userHelpers";

export const Misc = () => {
      const user = getUser();
      return (
        <div>
          <App />
        </div>
      );
};