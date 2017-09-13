var chart = c3.generate({
	bindto: "#sales_chart",
    data: {
		x: "day",
        url: '../sales_api',
		mimeType: 'json',
		type: "area-spline",
    },
	axis: {
		x: {
			type: 'timeseries',
			tick: {
				format: '%Y-%m-%d',
			},
		},
	}
});
