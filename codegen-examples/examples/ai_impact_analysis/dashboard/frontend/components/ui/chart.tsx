"use client";

import * as React from "react";
import { useEffect, useRef } from "react";
import * as RechartsPrimitive from "recharts";

import { cn } from "@/lib/utils";

// Format: { THEME_NAME: CSS_SELECTOR }
const THEMES = { light: "", dark: ".dark" } as const;

export type ChartConfig = {
	[key: string]: {
		theme?: Record<string, string>;
		color?: string;
	};
};

type ChartContextProps = {
	chartId: string;
};

const ChartContext = React.createContext<ChartContextProps>({
	chartId: "",
});

const useChart = () => {
	const context = React.useContext(ChartContext);

	if (!context) {
		throw new Error("useChart must be used within a ChartProvider");
	}

	return context;
};

const ChartContainer = React.forwardRef<
	HTMLDivElement,
	React.HTMLAttributes<HTMLDivElement> & {
		config?: ChartConfig;
	}
>(({ children, config = {}, className, ...props }, ref) => {
	const chartId = React.useId();

	return (
		<ChartContext.Provider value={{ chartId }}>
			<div
				ref={ref}
				data-chart={chartId}
				className={cn("w-full h-full", className)}
				{...props}
			>
				<ChartThemeStyles
					id={chartId}
					colorConfig={Object.entries(config).filter(
						([_, config]) => config.theme || config.color,
					)}
				/>
				<RechartsPrimitive.ResponsiveContainer>
					{children}
				</RechartsPrimitive.ResponsiveContainer>
			</div>
		</ChartContext.Provider>
	);
});
ChartContainer.displayName = "Chart";

// Add ChartThemeStylesProps type
type ChartThemeStylesProps = {
	id: string;
	colorConfig: [string, { theme?: Record<string, string>; color?: string }][];
};

const ChartThemeStyles = ({ id, colorConfig }: ChartThemeStylesProps) => {
	if (!colorConfig.length) {
		return null;
	}

	const styleContent = Object.entries(THEMES)
		.map(
			([theme, prefix]) => `
${prefix} [data-chart=${id}] {
${colorConfig
	.map(([key, itemConfig]) => {
		const color = itemConfig.theme?.[theme] || itemConfig.color;
		return color ? `  --color-${key}: ${color};` : null;
	})
	.filter(Boolean)
	.join("\n")}
}
`,
		)
		.join("\n");

	// Create a style element using useEffect to safely add styles
	const styleRef = useRef<HTMLStyleElement | null>(null);

	useEffect(() => {
		// Create style element if it doesn't exist
		if (!styleRef.current) {
			styleRef.current = document.createElement("style");
			document.head.appendChild(styleRef.current);
		}

		// Set the content
		styleRef.current.textContent = styleContent;

		// Cleanup on unmount
		return () => {
			if (styleRef.current) {
				document.head.removeChild(styleRef.current);
				styleRef.current = null;
			}
		};
	}, [styleContent]);

	// Return empty fragment as we're managing the style element via useEffect
	return <></>;
};

const ChartTooltip = RechartsPrimitive.Tooltip;

const ChartTooltipContent = React.forwardRef<
	HTMLDivElement,
	React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => {
	const { chartId } = useChart();

	return (
		<div
			ref={ref}
			data-chart={chartId}
			className={cn(
				"border bg-background p-2 shadow-md outline-none",
				className,
			)}
			{...props}
		/>
	);
});
ChartTooltipContent.displayName = "ChartTooltipContent";

const ChartLegend = RechartsPrimitive.Legend;

const ChartLegendContent = React.forwardRef<
	HTMLDivElement,
	React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => {
	const { chartId } = useChart();

	return (
		<div
			ref={ref}
			data-chart={chartId}
			className={cn("my-2 flex flex-wrap items-center gap-4", className)}
			{...props}
		/>
	);
});
ChartLegendContent.displayName = "ChartLegendContent";

function getConfigValue<T extends keyof ChartConfig>(
	config: ChartConfig,
	key: T,
	configLabelKey?: string,
) {
	return configLabelKey in config
		? config[configLabelKey]
		: config[key as keyof typeof config];
}

export {
	ChartContainer,
	ChartTooltip,
	ChartTooltipContent,
	ChartLegend,
	ChartLegendContent,
	ChartThemeStyles,
};
