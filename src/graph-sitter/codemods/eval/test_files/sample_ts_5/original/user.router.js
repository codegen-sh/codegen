const express = require("express");
const router = express.Router();

router.get("/user/:id", (req, res) => {
  res.json({ id: req.params.id, name: "John Doe" });
});

module.exports = router;
