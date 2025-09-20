import express from "express";
const router = express.Router();

router.get("/user/:id", (req, res) => {
  res.json({ id: req.params.id, name: "John Doe" });
});

export default router;
