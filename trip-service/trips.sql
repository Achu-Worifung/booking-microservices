
CREATE TABLE IF NOT EXISTS trips
(
    tripid uuid NOT NULL DEFAULT gen_random_uuid(),
    userid uuid NOT NULL,
    tripname character varying(255) ,
    destination character varying(255) ,
    startdate date NOT NULL,
    enddate date NOT NULL,
    travelers integer NOT NULL,
    budget numeric(10,2) NOT NULL,
    trip_status character varying(50) NOT NULL,
    description text ,
    createdat timestamp  NULL DEFAULT now(),
    updatedat timestamp  NOT NULL DEFAULT now(),
    
    CONSTRAINT trips_pkey PRIMARY KEY (tripid)
)

drop table trips