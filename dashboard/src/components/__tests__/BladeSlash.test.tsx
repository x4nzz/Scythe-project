import { render, screen } from "@testing-library/react";
import { BladeSlash } from "@/components/BladeSlash";

test("renders blade slash element", () => {
  render(<BladeSlash />);
  expect(screen.getByTestId("blade-slash")).toBeInTheDocument();
});