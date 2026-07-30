import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

import Card from "../common/Card";
import EmptyState from "../common/EmptyState";
import { AXIS_COLOR, GRID_COLOR, tooltipStyle } from "./chartTheme";

export default function CategoryChart({ data = [] }) {
  return (
    <Card title="Incidents by category">
      {data.length === 0 ? (
        <EmptyState title="No category data" />
      ) : (
        <ResponsiveContainer width="100%" height={270}>
          <BarChart data={data} margin={{ top: 8, right: 8, bottom: 24, left: -12 }}>
            <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="category"
              stroke={AXIS_COLOR}
              fontSize={11}
              interval={0}
              angle={-18}
              textAnchor="end"
              tickLine={false}
            />
            <YAxis stroke={AXIS_COLOR} fontSize={11} allowDecimals={false} tickLine={false} />
            <Tooltip
              contentStyle={tooltipStyle.contentStyle}
              itemStyle={tooltipStyle.itemStyle}
              labelStyle={tooltipStyle.labelStyle}
              cursor={tooltipStyle.cursor}
            />
            <Bar dataKey="count" fill="#3b82f6" radius={[5, 5, 0, 0]} maxBarSize={38} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
