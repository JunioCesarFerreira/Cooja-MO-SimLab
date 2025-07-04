#ifndef PROJECT_CONF_H_
#define PROJECT_CONF_H_

#define ENERGEST_CONF_ON 1

#define TSCH_CONF_DEFAULT_LENGTH          11
#define TSCH_CONF_DEFAULT_TIMESLOT_LENGTH 8000  /* 8 ms @ 1 MHz */
#define TSCH_CONF_MAX_TX_RETRIES          3
#define TSCH_CONF_EB_PERIOD               (8 * CLOCK_SECOND)
#define QUEUEBUF_CONF_NUM                 16

#endif /* PROJECT_CONF_H_ */
