import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";

import Card from "../common/Card";
import EmptyState from "../common/EmptyState";
import { AXIS_COLOR, GRID_COLOR, tooltipStyle } from "./chartTheme";

export default function TrendChart({ data = [] }) {
  return (
    <Card title="Incident trend">
      {data.length === 0 ? (
        <EmptyState title="No trend data" />
      ) : (
        <ResponsiveContainer width="100%" height={270}>
          <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
            <defs>
              <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.45} />
                <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>

            <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="date" stroke={AXIS_COLOR} fontSize={11} tickLine={false} />
            <YAxis stroke={AXIS_COLOR} fontSize={11} allowDecimals={false} tickLine={false} />
            <Tooltip
              contentStyle={tooltipStyle.contentStyle}
              itemStyle={tooltipStyle.itemStyle}
              labelStyle={tooltipStyle.labelStyle}
            />
            <Area
              type="monotone"
              dataKey="count"
              stroke="#3b82f6"
              strokeWidth={2}
              fill="url(#trendFill)"
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
