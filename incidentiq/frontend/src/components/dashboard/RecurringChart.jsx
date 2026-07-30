import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

import Card from "../common/Card";
import EmptyState from "../common/EmptyState";
import { AXIS_COLOR, GRID_COLOR, tooltipStyle } from "./chartTheme";

export default function RecurringChart({ data = [] }) {
  return (
    <Card title="Recurring root causes">
      {data.length === 0 ? (
        <EmptyState title="No recurring issues" />
      ) : (
        <ResponsiveContainer width="100%" height={270}>
          <BarChart data={data} layout="vertical" margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
            <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3" horizontal={false} />
            <XAxis
              type="number"
              stroke={AXIS_COLOR}
              fontSize={11}
              allowDecimals={false}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="cause"
              width={170}
              stroke={AXIS_COLOR}
              fontSize={11}
              tickLine={false}
            />
            <Tooltip
              contentStyle={tooltipStyle.contentStyle}
              itemStyle={tooltipStyle.itemStyle}
              labelStyle={tooltipStyle.labelStyle}
              cursor={tooltipStyle.cursor}
            />
            <Bar dataKey="count" fill="#a855f7" radius={[0, 5, 5, 0]} maxBarSize={20} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
