"use client";

import { ContributionTimeline } from "@/components/contribution-timeline";
import { ContributorsBreakdown } from "@/components/contributors-breakdown";
import { DashboardHeader } from "@/components/dashboard-header";
import { HighImpactSymbols } from "@/components/high-impact-symbols";
import { LoadingScreen } from "@/components/loading-screen";
import { SummaryCards } from "@/components/summary-cards";
import { TopAIFiles } from "@/components/top-ai-files";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { AnalysisData } from "@/lib/types";
import { GitBranch, Loader2 } from "lucide-react";
import { useState } from "react";

export function RepoAnalysisDashboard() {
	const [data, setData] = useState<AnalysisData | null>(null);
	const [loading, setLoading] = useState(false);
	const [repoUrl, setRepoUrl] = useState("");

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault();
		if (repoUrl.trim()) {
			setLoading(true);
			const match = repoUrl.match(/(?:github\.com\/)?([^/\s]+\/[^/\s]+)/);
			if (match) {
				const repoFullName = match[1];
				fetch(
					`[your-modal-deployment-url]/analyze?repo_full_name=${repoFullName}`,
					{
						method: "POST",
					},
				)
					.then((response) => {
						if (!response.ok) {
							throw new Error("Network response was not ok");
						}
						return response.json();
					})
					.then((analysisData: AnalysisData) => {
						setData(analysisData);
						setLoading(false);
					})
					.catch((error) => {
						console.error("Error analyzing repository:", error);
						setLoading(false);
					});
			}
		}
	};

	return (
		<div className="container mx-auto py-6 space-y-8">
			{loading && <LoadingScreen />}

			<DashboardHeader />

			<Card>
				<CardContent className="pt-6">
					<form onSubmit={handleSubmit} className="space-y-4">
						<div className="flex flex-col space-y-2">
							<label htmlFor="repo-url" className="text-sm font-medium">
								Repository Slug
							</label>
							<div className="flex space-x-2">
								<div className="relative flex-1 mr-2">
									<GitBranch className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
									<Input
										id="repo-url"
										placeholder="username/repo"
										className="pl-10"
										value={repoUrl}
										onChange={(e) => setRepoUrl(e.target.value)}
										disabled={loading}
									/>
								</div>
								<Button type="submit" disabled={loading || !repoUrl.trim()}>
									{loading ? (
										<>
											<Loader2 className="mr-2 h-4 w-4 animate-spin" />
											Analyzing...
										</>
									) : (
										"Analyze Repo"
									)}
								</Button>
							</div>
						</div>
					</form>
				</CardContent>
			</Card>

			{data && (
				<div className="space-y-8">
					<SummaryCards data={data} />

					<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
						<ContributionTimeline timeline={data.timeline} />
						<ContributorsBreakdown contributors={data.contributors} />
					</div>

					<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
						<TopAIFiles files={data.stats.top_ai_files} />
						<HighImpactSymbols symbols={data.high_impact_symbols} />
					</div>
				</div>
			)}
			<br></br>
			<br></br>
		</div>
	);
}
