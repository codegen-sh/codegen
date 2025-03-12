"use client";

import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
	Cell,
	Legend,
	Pie,
	PieChart,
	ResponsiveContainer,
	Tooltip,
} from "recharts";

interface ContributorsBreakdownProps {
	contributors: [string, number][];
}

export function ContributorsBreakdown({
	contributors,
}: ContributorsBreakdownProps) {
	// Take top 5 contributors for the chart
	const topContributors = contributors.slice(0, 5);
	const otherContributors = contributors.slice(5);
	const otherCount = otherContributors.reduce(
		(sum, [_, count]) => sum + count,
		0,
	);

	const chartData = [
		...topContributors.map(([name, count]) => ({
			name: name.split(" ")[0], // Just use first name for chart
			fullName: name,
			count,
		})),
		otherContributors.length > 0
			? { name: "Others", fullName: "Other Contributors", count: otherCount }
			: null,
	].filter(Boolean);

	const COLORS = [
		"#3b82f6",
		"#10b981",
		"#f59e0b",
		"#ef4444",
		"#8b5cf6",
		"#6b7280",
	];

	return (
		<Card className="col-span-1">
			<CardHeader>
				<CardTitle>Contributors Breakdown</CardTitle>
				<CardDescription>Top contributors by commit count</CardDescription>
			</CardHeader>
			<CardContent className="h-[300px]">
				<div className="flex h-full">
					<div className="w-1/2 h-full">
						<ResponsiveContainer width="100%" height="100%">
							<PieChart>
								<Pie
									data={chartData}
									cx="50%"
									cy="50%"
									innerRadius={60}
									outerRadius={80}
									paddingAngle={2}
									dataKey="count"
								>
									{chartData.map((entry, index) => (
										<Cell
											key={`cell-${index}`}
											fill={COLORS[index % COLORS.length]}
										/>
									))}
								</Pie>
								<Tooltip
									formatter={(value, name, props) => [
										value,
										props.payload.fullName,
									]}
									contentStyle={{
										backgroundColor: "white",
										borderColor: "#e2e8f0",
										borderRadius: "0.375rem",
									}}
								/>
								<Legend />
							</PieChart>
						</ResponsiveContainer>
					</div>
					<div className="w-1/2 h-full">
						<ScrollArea className="h-full pr-4">
							<div className="space-y-2">
								{contributors.slice(0, 10).map(([name, count], index) => (
									<div
										key={name}
										className="flex justify-between items-center text-sm"
									>
										<div className="flex items-center">
											<div
												className="w-3 h-3 rounded-full mr-2"
												style={{
													backgroundColor: COLORS[index % COLORS.length],
												}}
											/>
											<span className="truncate max-w-[150px]">
												{name.split(" ")[0]}
											</span>
										</div>
										<div>{count}</div>
									</div>
								))}
								{contributors.length > 10 && (
									<div className="text-xs text-muted-foreground text-center pt-2">
										+{contributors.length - 10} more contributors
									</div>
								)}
							</div>
						</ScrollArea>
					</div>
				</div>
			</CardContent>
		</Card>
	);
}
