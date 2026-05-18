export function summarizeStatus(config) {
  const activeMaintenance = Boolean(config.maintenance?.enabled);
  const degradedServices = config.services.filter((service) => service.status !== "operational");

  if (activeMaintenance) {
    return {
      level: "maintenance",
      label: "Scheduled maintenance",
      affected: config.maintenance.serviceName
    };
  }

  if (degradedServices.length > 0) {
    return {
      level: "degraded",
      label: "Service degradation",
      affected: degradedServices.map((service) => service.name).join(", ")
    };
  }

  return {
    level: "operational",
    label: "All systems operational",
    affected: null
  };
}

export function publicStatusPayload(config) {
  return {
    generatedAt: config.generatedAt,
    overallStatus: config.overallStatus,
    summary: summarizeStatus(config),
    services: config.services,
    maintenance: config.maintenance
  };
}

