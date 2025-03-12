"use client";

import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import type { Timeline } from "@/lib/types";
import {
	Bar,
	BarChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";

interface ContributionTimelineProps {
	timeline: Timeline[];
}

export function ContributionTimeline({ timeline }: ContributionTimelineProps) {
	return (
		<Card className="col-span-1">
			<CardHeader>
				<CardTitle>AI Contribution Timeline</CardTitle>
				<CardDescription>Monthly AI contributions over time</CardDescription>
			</CardHeader>
			<CardContent className="h-[300px]">
				<ResponsiveContainer width="100%" height="100%">
					<BarChart data={timeline}>
						<XAxis
							dataKey="date"
							stroke="#888888"
							fontSize={12}
							tickLine={false}
							axisLine={false}
						/>
						<YAxis
							stroke="#888888"
							fontSize={12}
							tickLine={false}
							axisLine={false}
							tickFormatter={(value) => `${value}`}
						/>
						<Tooltip
							content={({ active, payload }) => {
								if (active && payload && payload.length) {
									return (
										<div className="rounded-lg border bg-background p-2 shadow-sm">
											<div className="grid grid-cols-2 gap-2">
												<div className="flex flex-col">
													<span className="text-[0.70rem] uppercase text-muted-foreground">
														Date
													</span>
													<span className="font-bold text-foreground">
														{payload[0].payload.date}
													</span>
												</div>
												<div className="flex flex-col">
													<span className="text-[0.70rem] uppercase text-muted-foreground">
														Commits
													</span>
													<span className="font-bold text-foreground">
														{payload[0].value}
													</span>
												</div>
											</div>
										</div>
									);
								}
								return null;
							}}
						/>
						<Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
					</BarChart>
				</ResponsiveContainer>
			</CardContent>
		</Card>
	);
}
