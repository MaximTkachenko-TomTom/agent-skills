---
name: call-routing-api
descrition: Call TomTom routing API to build a route.
---

When asked to create a route between two or more geo points, use this endpoint.

# Parameters

- API key can be found in `TOMTOM_API_KEY` environment variable.
- routePlaningLocations shall be in the user prompt.
- Other usual options are
```
key=${TOMTOM_API_KEY}&apiVersion=2&routeRepresentation=encodedPolyline&instructionsType=coded&language=en-US&extendedRouteRepresentation=distance&extendedRouteRepresentation=travelTime&&routeType=fast&guidanceVersion=2&instructionPhonetics=IPA&instructionRoadShieldReferences=all&sectionType=roadShields&sectionType=lanes&travelMode=car"
```

# TomTom endpoint

Use the Orbis routing endpoint:
```
https://api.tomtom.com/maps/orbis/routing/calculateRoute/{routePlanningLocations}/{contentType}?key={Your_API_Key}
&callback={callback}
&maxAlternatives={alternativeRoutes}
&alternativeType={alternativeType}
&minDeviationDistance={integer}
&minDeviationTime={integer}
&supportingPointIndexOfOrigin={integer}
&computeBestOrder={boolean}
&routeRepresentation={routeRepresentation}
&computeTravelTimeFor={trafficTypes}
&vehicleHeading={integer}
&language={language}
&sectionType={sectionType}
&includeTollPaymentTypes={includeTollPaymentTypes}
&report={effectiveSettings}
&departAt={time}
&arriveAt={time}
&routeType={routeType}
&traffic={boolean}
&avoid={avoidType}
&travelMode={travelMode}
&hilliness={hilliness}
&windingness={windingness}
&vehicleMaxSpeed={vehicleMaxSpeed}
&vehicleWeight={vehicleWeight}
&vehicleAxleWeight={vehicleAxleWeight}
&vehicleNumberOfAxles={vehicleNumberOfAxles}
&vehicleLength={vehicleLength}
&vehicleWidth={vehicleWidth}
&vehicleHeight={vehicleHeight}
&vehicleCommercial={boolean}
&vehicleLoadType={vehicleLoadType}
&vehicleAdrTunnelRestrictionCode={vehicleAdrTunnelRestrictionCode}
&vehicleEngineType={vehicleEngineType}
&constantSpeedConsumptionInLitersPerHundredkm={CombustionConstantSpeedConsumptionPairs}
&currentFuelInLiters={float}
&auxiliaryPowerInLitersPerHour={float}
&fuelEnergyDensityInMJoulesPerLiter={float}
&accelerationEfficiency={float}
&decelerationEfficiency={float}
&uphillEfficiency={float}
&downhillEfficiency={float}
&consumptionInkWhPerkmAltitudeGain={float}
&recuperationInkWhPerkmAltitudeLoss={float}
&constantSpeedConsumptionInkWhPerHundredkm={ElectricConstantSpeedConsumptionPairs}
&currentChargeInkWh={float}
&maxChargeInkWh={float}
&auxiliaryPowerInkW={float}
&chargeMarginsInkWh={commaSeparatedFloats}
&extendedRouteRepresentation={extendedRouteRepresentation}
```

# Full API documentation

If somehting goes wrong with API requests, read the full developer documentarion at address
https://developer.tomtom.com/routing-api/documentation/tomtom-maps/calculate-route
